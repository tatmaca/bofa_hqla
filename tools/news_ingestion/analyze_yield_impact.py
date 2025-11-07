#!/usr/bin/env python3
"""
LLM Agent for Yield Curve Impact Analysis
Analyzes bucketed news and predicts impact on different tenors of the yield curve.
"""

import os
import json
import yaml
import sqlite3
import datetime as dt
import time
from datetime import timezone
from typing import Dict, List, Optional
from pathlib import Path

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("[WARN] OpenAI not installed. Install with: pip install openai")

DB_PATH = os.environ.get("NEWS_DB_PATH", "news.db")
CONFIG_PATH = "news_config.yaml"

TENORS = ["2y", "5y", "10y", "30y"]
SPREADS = ["2s10s", "2s30s"]

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_bucketed_news(date: Optional[str] = None) -> Dict[str, List[Dict]]:
    """Get news articles grouped by bucket for a given date."""
    if date is None:
        date = dt.date.today().isoformat()
    
    with get_conn() as c:
        rows = c.execute("""
            SELECT bucket, title, text, summary, source, url, bucket_confidence
            FROM articles
            WHERE DATE(COALESCE(published_at, fetched_at)) = DATE(?)
              AND bucket IS NOT NULL
              AND bucket != ''
            ORDER BY bucket_confidence DESC, published_at DESC
        """, (date,)).fetchall()
    
    buckets = {}
    for row in rows:
        bucket = row["bucket"]
        if bucket not in buckets:
            buckets[bucket] = []
        buckets[bucket].append(dict(row))
    
    return buckets

def call_openai_with_retry(client, messages, model="gpt-4o", max_retries=3, **kwargs):
    """Call OpenAI API with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return response
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                error_msg = str(e).lower()
                if "rate limit" in error_msg:
                    wait_time = min(wait_time * 2, 60)  # Longer wait for rate limits
                print(f"[RETRY] Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    return None

def validate_analysis_response(result: Dict) -> Dict:
    """Validate and fix analysis response structure."""
    # Ensure all required fields exist
    if "predictions" not in result:
        result["predictions"] = {}
    if "spreads" not in result:
        result["spreads"] = {}
    
    # Validate predictions
    for tenor in TENORS:
        if tenor not in result["predictions"]:
            result["predictions"][tenor] = {"direction": "flat", "magnitude_bps": 0.0, "reasoning": "Missing prediction"}
        else:
            pred = result["predictions"][tenor]
            # Ensure direction is valid
            if pred.get("direction") not in ["up", "down", "flat"]:
                pred["direction"] = "flat"
            # Ensure magnitude is a number
            try:
                pred["magnitude_bps"] = float(pred.get("magnitude_bps", 0.0))
            except (ValueError, TypeError):
                pred["magnitude_bps"] = 0.0
    
    # Validate spreads
    for spread in SPREADS:
        if spread not in result["spreads"]:
            result["spreads"][spread] = {"direction": "flat", "magnitude_bps": 0.0, "reasoning": "Missing prediction"}
        else:
            spred = result["spreads"][spread]
            if spred.get("direction") not in ["steepen", "flatten", "flat"]:
                spred["direction"] = "flat"
            try:
                spred["magnitude_bps"] = float(spred.get("magnitude_bps", 0.0))
            except (ValueError, TypeError):
                spred["magnitude_bps"] = 0.0
    
    if "overall_summary" not in result:
        result["overall_summary"] = "Analysis completed"
    
    return result

def analyze_yield_impact(bucketed_news: Dict[str, List[Dict]], 
                       current_curve: Optional[Dict] = None,
                       api_key: Optional[str] = None) -> Dict:
    """
    Use LLM to analyze news buckets and predict yield curve impact.
    
    Returns:
    {
        "predictions": {
            "2y": {"direction": "up/down/flat", "magnitude_bps": float, "reasoning": str},
            ...
        },
        "spreads": {
            "2s10s": {"direction": "steepen/flatten/flat", "magnitude_bps": float, "reasoning": str},
            ...
        },
        "overall_summary": str
    }
    """
    if not HAS_OPENAI:
        return get_fallback_prediction()
    
    # Initialize OpenAI client
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key and os.path.exists(CONFIG_PATH):
        cfg = yaml.safe_load(open(CONFIG_PATH))
        api_key = cfg.get("openai_api_key")
    
    if not api_key:
        print("[WARN] No OpenAI API key found. Using fallback prediction.")
        return get_fallback_prediction()
    
    client = OpenAI(api_key=api_key)
    
    # Prepare detailed news summary by bucket
    news_summary = []
    for bucket, articles in bucketed_news.items():
        if not articles:
            continue
        # Take top articles per bucket (by confidence), up to 8 per bucket
        top_articles = articles[:8]
        bucket_info = [f"{bucket.upper()} ({len(articles)} articles):"]
        
        for i, article in enumerate(top_articles[:5], 1):
            title = article.get("title", "No title")
            summary = article.get("summary", "")
            # Include summary if available and not too long
            if summary and len(summary) < 200:
                bucket_info.append(f"  {i}. {title} | {summary[:150]}")
            else:
                bucket_info.append(f"  {i}. {title}")
        
        news_summary.append("\n".join(bucket_info))
    
    news_text = "\n\n".join(news_summary)
    
    # Current curve context (if available)
    curve_context = ""
    delta_context = ""
    if current_curve:
        zeros = current_curve.get("zeros_pct", {})
        spreads = current_curve.get("spreads_pct", {})
        delta = current_curve.get("delta", {})
        delta_zeros = delta.get("zeros_pct", {})
        delta_spreads = delta.get("spreads_pct", {})
        
        # Format yield values safely
        def fmt_yield(val, default='N/A'):
            if isinstance(val, (int, float)):
                return f"{val:.2f}"
            return str(default)
        
        curve_context = f"""
CURRENT YIELD CURVE STATE (as of {current_curve.get('as_of', 'today')}):
- 2y: {fmt_yield(zeros.get('2y'), 'N/A')}%
- 5y: {fmt_yield(zeros.get('5y'), 'N/A')}%
- 10y: {fmt_yield(zeros.get('10y'), 'N/A')}%
- 30y: {fmt_yield(zeros.get('30y'), 'N/A')}%
- 2s10s spread: {fmt_yield(spreads.get('2s10s'), 'N/A')}%
- 2s30s spread: {fmt_yield(spreads.get('2s30s'), 'N/A')}%
"""
        
        if delta_zeros or delta_spreads:
            delta_context = f"""
RECENT MOVEMENT (vs previous day):
- 2y: {delta_zeros.get('2y', 0.0):+.2f}% ({'↑' if delta_zeros.get('2y', 0) > 0 else '↓' if delta_zeros.get('2y', 0) < 0 else '→'})
- 5y: {delta_zeros.get('5y', 0.0):+.2f}%
- 10y: {delta_zeros.get('10y', 0.0):+.2f}%
- 30y: {delta_zeros.get('30y', 0.0):+.2f}%
- 2s10s spread: {delta_spreads.get('2s10s', 0.0):+.2f}% ({'steepened' if delta_spreads.get('2s10s', 0) > 0 else 'flattened' if delta_spreads.get('2s10s', 0) < 0 else 'unchanged'})
- 2s30s spread: {delta_spreads.get('2s30s', 0.0):+.2f}%
"""
    
    prompt = f"""You are a senior fixed income strategist at a major investment bank analyzing how news events impact U.S. Treasury yield curves. Your analysis will inform trading decisions.

{curve_context}{delta_context}

NEWS EVENTS (last 24 hours):
{news_text}

TASK: Analyze how these news events are likely to impact U.S. Treasury yields over the next trading session.

YIELD CURVE TENOR CHARACTERISTICS:
- 2y (2-year): Most sensitive to Federal Reserve policy expectations and short-term rate outlook. Moves quickly on Fed signals.
- 5y (5-year): Intermediate term, sensitive to economic growth outlook and medium-term inflation expectations. Often reflects market's view on economic cycle.
- 10y (10-year): Benchmark rate, sensitive to growth expectations, inflation outlook, and risk sentiment. Widely watched indicator.
- 30y (30-year): Long-term rate, sensitive to long-term inflation expectations, fiscal policy, and supply/demand dynamics. Less volatile but reflects structural views.

SPREAD ANALYSIS:
- 2s10s (10y - 2y): Widening (steepening) suggests growth/inflation expectations rising faster than Fed policy. Narrowing (flattening) suggests Fed tightening expectations or risk-off.
- 2s30s (30y - 2y): Similar to 2s10s but reflects longer-term structural views. Steepening often indicates inflation concerns.

ANALYSIS GUIDELINES:
1. Consider the magnitude and direction of impact for each tenor
2. Magnitude should be in basis points (bps). Typical daily moves: 1-5 bps (normal), 5-15 bps (significant), 15+ bps (major event)
3. Consider how different news buckets interact (e.g., monetary policy + economic data)
4. If news is mixed or neutral, predict "flat" with 0-2 bps magnitude
5. Provide clear reasoning linking specific news to yield impact
6. Consider current curve shape - if already steep/flat, news impact may differ

Respond with ONLY valid JSON in this exact format (no markdown, no code blocks):
{{
    "predictions": {{
        "2y": {{"direction": "up|down|flat", "magnitude_bps": <number>, "reasoning": "<2-3 sentence explanation>"}},
        "5y": {{"direction": "up|down|flat", "magnitude_bps": <number>, "reasoning": "<2-3 sentence explanation>"}},
        "10y": {{"direction": "up|down|flat", "magnitude_bps": <number>, "reasoning": "<2-3 sentence explanation>"}},
        "30y": {{"direction": "up|down|flat", "magnitude_bps": <number>, "reasoning": "<2-3 sentence explanation>"}}
    }},
    "spreads": {{
        "2s10s": {{"direction": "steepen|flatten|flat", "magnitude_bps": <number>, "reasoning": "<2-3 sentence explanation>"}},
        "2s30s": {{"direction": "steepen|flatten|flat", "magnitude_bps": <number>, "reasoning": "<2-3 sentence explanation>"}}
    }},
    "overall_summary": "<3-4 sentence summary of expected curve movement and key drivers>"
}}
"""

    try:
        messages = [
            {
                "role": "system", 
                "content": "You are a senior fixed income strategist with 20+ years of experience analyzing Treasury markets. You provide precise, data-driven analysis. Always respond with valid JSON only, no markdown formatting."
            },
            {"role": "user", "content": prompt}
        ]
        
        response = call_openai_with_retry(
            client,
            messages,
            model="gpt-4o",
            temperature=0.3,  # Lower temperature for more consistent, accurate predictions
            max_tokens=2000,  # Increased for more detailed reasoning
            response_format={"type": "json_object"}  # Force JSON output
        )
        
        if not response:
            raise Exception("Failed to get response after retries")
        
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse JSON directly first
        try:
            result = json.loads(result_text)
        except json.JSONDecodeError:
            # If direct parse fails, try to extract JSON from markdown
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            result = json.loads(result_text)
        
        # Validate and fix response structure
        result = validate_analysis_response(result)
        return result
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse LLM response as JSON: {e}")
        print(f"[DEBUG] Response text: {result_text[:500]}")
        return get_fallback_prediction()
    except Exception as e:
        print(f"[ERROR] LLM analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return get_fallback_prediction()

def get_fallback_prediction() -> Dict:
    """Fallback prediction when LLM is unavailable."""
    return {
        "predictions": {
            "2y": {"direction": "flat", "magnitude_bps": 0.0, "reasoning": "Fallback: no analysis available"},
            "5y": {"direction": "flat", "magnitude_bps": 0.0, "reasoning": "Fallback: no analysis available"},
            "10y": {"direction": "flat", "magnitude_bps": 0.0, "reasoning": "Fallback: no analysis available"},
            "30y": {"direction": "flat", "magnitude_bps": 0.0, "reasoning": "Fallback: no analysis available"}
        },
        "spreads": {
            "2s10s": {"direction": "flat", "magnitude_bps": 0.0, "reasoning": "Fallback: no analysis available"},
            "2s30s": {"direction": "flat", "magnitude_bps": 0.0, "reasoning": "Fallback: no analysis available"}
        },
        "overall_summary": "Analysis unavailable - LLM service not configured"
    }

def load_curve_snapshot(date: Optional[str] = None) -> Optional[Dict]:
    """Load yield curve snapshot for a given date."""
    if date is None:
        date = dt.date.today().isoformat()
    
    # Try to load from ust_curve snapshots
    repo_root = Path(__file__).resolve().parents[2]
    snapshot_path = repo_root / "tools" / "ust_curve" / "llm" / "snapshots" / f"curve_snapshot_{date}.json"
    
    if snapshot_path.exists():
        with open(snapshot_path) as f:
            return json.load(f)
    
    return None

def save_analysis(date: str, analysis: Dict, bucketed_news: Dict[str, List[Dict]]):
    """Save analysis results."""
    output_dir = Path(__file__).parent / "analyses"
    output_dir.mkdir(exist_ok=True)
    
    output = {
        "date": date,
        "analysis": analysis,
        "news_summary": {
            bucket: len(articles) for bucket, articles in bucketed_news.items()
        },
        "created_at": dt.datetime.now(timezone.utc).isoformat()
    }
    
    output_path = output_dir / f"yield_impact_{date}.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"[ANALYSIS] Saved to {output_path}")
    return output_path

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Analyze yield curve impact from news")
    ap.add_argument("--date", type=str, help="Date (YYYY-MM-DD), defaults to today")
    ap.add_argument("--api-key", type=str, help="OpenAI API key")
    args = ap.parse_args()
    
    date = args.date or dt.date.today().isoformat()
    
    print(f"[ANALYSIS] Analyzing yield impact for {date}")
    
    # Get bucketed news
    bucketed_news = get_bucketed_news(date)
    if not bucketed_news:
        print(f"[WARN] No bucketed news found for {date}")
        return
    
    print(f"[ANALYSIS] Found news in {len(bucketed_news)} buckets")
    
    # Load current curve snapshot
    current_curve = load_curve_snapshot(date)
    
    # Get API key
    api_key = args.api_key
    if not api_key and os.path.exists(CONFIG_PATH):
        cfg = yaml.safe_load(open(CONFIG_PATH))
        api_key = cfg.get("openai_api_key") or os.environ.get("OPENAI_API_KEY")
    
    # Analyze
    analysis = analyze_yield_impact(bucketed_news, current_curve, api_key)
    
    # Print summary
    print("\n=== YIELD CURVE IMPACT ANALYSIS ===")
    print(f"\nOverall: {analysis.get('overall_summary', 'N/A')}\n")
    
    print("Tenor Predictions:")
    for tenor, pred in analysis.get("predictions", {}).items():
        print(f"  {tenor}: {pred['direction']} {pred['magnitude_bps']:.1f}bps - {pred['reasoning']}")
    
    print("\nSpread Predictions:")
    for spread, pred in analysis.get("spreads", {}).items():
        print(f"  {spread}: {pred['direction']} {pred['magnitude_bps']:.1f}bps - {pred['reasoning']}")
    
    # Save
    save_analysis(date, analysis, bucketed_news)

if __name__ == "__main__":
    main()

