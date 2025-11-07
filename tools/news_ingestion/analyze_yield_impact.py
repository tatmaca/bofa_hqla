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
from datetime import timezone
from typing import Dict, List, Optional
from pathlib import Path

try:
    import openai
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
    
    if api_key:
        openai.api_key = api_key
    elif os.environ.get("OPENAI_API_KEY"):
        openai.api_key = os.environ.get("OPENAI_API_KEY")
    else:
        print("[WARN] No OpenAI API key found. Using fallback prediction.")
        return get_fallback_prediction()
    
    # Prepare news summary by bucket
    news_summary = []
    for bucket, articles in bucketed_news.items():
        if not articles:
            continue
        # Take top articles per bucket (by confidence)
        top_articles = articles[:5]  # Limit to top 5 per bucket
        titles = [a.get("title", "") for a in top_articles if a.get("title")]
        news_summary.append(f"{bucket.upper()}: {len(articles)} articles. Top headlines: {'; '.join(titles[:3])}")
    
    news_text = "\n".join(news_summary)
    
    # Current curve context (if available)
    curve_context = ""
    if current_curve:
        zeros = current_curve.get("zeros_pct", {})
        spreads = current_curve.get("spreads_pct", {})
        curve_context = f"""
Current Yield Curve (as of {current_curve.get('as_of', 'today')}):
- 2y: {zeros.get('2y', 'N/A')}%
- 5y: {zeros.get('5y', 'N/A')}%
- 10y: {zeros.get('10y', 'N/A')}%
- 30y: {zeros.get('30y', 'N/A')}%
- 2s10s spread: {spreads.get('2s10s', 'N/A')}%
- 2s30s spread: {spreads.get('2s30s', 'N/A')}%
"""
    
    prompt = f"""You are a fixed income strategist analyzing how news events impact U.S. Treasury yield curves.

{curve_context}

News Summary (last 24 hours):
{news_text}

Analyze how these news events are likely to impact different tenors of the U.S. Treasury yield curve:
- 2y (2-year): Most sensitive to Fed policy expectations
- 5y (5-year): Intermediate term, sensitive to economic outlook
- 10y (10-year): Benchmark rate, sensitive to growth and inflation expectations
- 30y (30-year): Long-term rate, sensitive to inflation and fiscal policy

Also analyze impact on spreads:
- 2s10s: 10y minus 2y (steepening = widening, flattening = narrowing)
- 2s30s: 30y minus 2y

Respond with ONLY a JSON object in this exact format:
{{
    "predictions": {{
        "2y": {{"direction": "up|down|flat", "magnitude_bps": float, "reasoning": "explanation"}},
        "5y": {{"direction": "up|down|flat", "magnitude_bps": float, "reasoning": "explanation"}},
        "10y": {{"direction": "up|down|flat", "magnitude_bps": float, "reasoning": "explanation"}},
        "30y": {{"direction": "up|down|flat", "magnitude_bps": float, "reasoning": "explanation"}}
    }},
    "spreads": {{
        "2s10s": {{"direction": "steepen|flatten|flat", "magnitude_bps": float, "reasoning": "explanation"}},
        "2s30s": {{"direction": "steepen|flatten|flat", "magnitude_bps": float, "reasoning": "explanation"}}
    }},
    "overall_summary": "2-3 sentence summary of expected curve movement"
}}
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",  # Use more capable model for analysis
            messages=[
                {"role": "system", "content": "You are an expert fixed income strategist. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=1000
        )
        
        result_text = response.choices[0].message.content.strip()
        # Extract JSON from response
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(result_text)
        return result
        
    except Exception as e:
        print(f"[WARN] LLM analysis failed: {e}")
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

