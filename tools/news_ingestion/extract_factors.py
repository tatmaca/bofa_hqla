#!/usr/bin/env python3
"""
Factor Extraction System
Extracts specific economic factors from news articles for linear online learning model.
Based on ONYL (Online News→Yield Learner) algorithm requirements.

Factors extracted:
- Monetary: FED_TONE, FED_PATH_SURPRISE, POLICY_RATE_SURPRISE, BAL_SHEET_QT_QE
- Inflation/Growth: CPI_CORE_SURP, PCE_CORE_SURP, NFP_SURP, WAGE_SURP, ISM_SURP, INFL_EXP_SURP
- Supply/Fiscal: SUPPLY_LONG, SUPPLY_BILLS, FISCAL_DEFICIT_NEWS, TERM_PREMIUM_NEWS
- Risk: RISK_OFF, RISK_ON, MOVE_SHIFT
- Energy/Housing: OIL_SHOCK_UP, OIL_SHOCK_DOWN, MBS_CONVEXITY, HOUSING_TURN, FUNDING_STRESS
- Global: ECB_TONE, BOE_TONE, YCC_JGB_SHIFT, CHINA_GROWTH_NEWS, GEO_EVENT
"""

import os
import sys
import json
import yaml
import datetime as dt
import time
import concurrent.futures
from datetime import timezone
from typing import List, Dict, Optional, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from db import get_conn

# Try to import OpenAI, but make it optional
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("[WARN] OpenAI not installed. Install with: pip install openai")

CONFIG_PATH = Path(__file__).parent / "news_config.yaml"

# All factors from PDFs
ALL_FACTORS = [
    # Monetary Policy
    "FED_TONE", "FED_PATH_SURPRISE", "POLICY_RATE_SURPRISE", "BAL_SHEET_QT_QE",
    # Inflation & Growth
    "CPI_CORE_SURP", "CPI_HEAD_SURP", "PCE_CORE_SURP", "NFP_SURP", "WAGE_SURP",
    "UNEMPLOYMENT_RATE_SURP", "ISM_SURP", "RETAIL_SALES_SURP", "GDP_SURP",
    "PRODUCTIVITY_SURP", "INFL_EXP_SURP",
    # Supply / Fiscal / Term Premium
    "SUPPLY_LONG", "SUPPLY_BILLS", "FISCAL_DEFICIT_NEWS", "TERM_PREMIUM_NEWS",
    # Risk & Vol
    "RISK_OFF", "RISK_ON", "MOVE_SHIFT",
    # Energy / Housing / Convexity / Funding
    "OIL_SHOCK_UP", "OIL_SHOCK_DOWN", "MBS_CONVEXITY", "HOUSING_TURN", "FUNDING_STRESS",
    # Global Spillovers
    "ECB_TONE", "ECB_RATE_SURP", "BOE_TONE", "BOE_RATE_SURP", "YCC_JGB_SHIFT",
    "CHINA_GROWTH_NEWS", "EU_GROWTH_NEWS", "GEO_EVENT"
]

FACTOR_DESCRIPTIONS = {
    "FED_TONE": "Federal Reserve hawkish↔dovish tone in speeches, pressers, or communications",
    "FED_PATH_SURPRISE": "Surprise in Fed dot plot, forward guidance, or rate path expectations",
    "POLICY_RATE_SURPRISE": "Actual policy rate change vs market pricing (rare outside FOMC)",
    "BAL_SHEET_QT_QE": "Quantitative tightening (QT) or quantitative easing (QE) emphasis, RRP/IOER tweaks",
    "CPI_CORE_SURP": "Core CPI surprise vs consensus (standardized)",
    "CPI_HEAD_SURP": "Headline CPI surprise vs consensus",
    "PCE_CORE_SURP": "Core PCE surprise vs consensus",
    "NFP_SURP": "Nonfarm payrolls surprise vs consensus",
    "WAGE_SURP": "Average hourly earnings (AHE) wage growth surprise",
    "UNEMPLOYMENT_RATE_SURP": "Unemployment rate surprise (negative = lower unemployment)",
    "ISM_SURP": "ISM Manufacturing or Services PMI surprise",
    "RETAIL_SALES_SURP": "Retail sales surprise vs consensus",
    "GDP_SURP": "GDP growth surprise vs consensus",
    "PRODUCTIVITY_SURP": "Productivity data surprise",
    "INFL_EXP_SURP": "Inflation expectations surprise (UMich 5y, surveys)",
    "SUPPLY_LONG": "10-30y Treasury refunding/auction size increase or decrease",
    "SUPPLY_BILLS": "Bill supply changes, TGA rebuild, short-term issuance",
    "FISCAL_DEFICIT_NEWS": "Fiscal deficit trajectory, shutdown risk, debt ceiling",
    "TERM_PREMIUM_NEWS": "Research notes or officials flagging higher term premium",
    "RISK_OFF": "Risk-off regime: equities down, credit wider, safe-haven bid (negative on yields)",
    "RISK_ON": "Risk-on regime: equities up, credit tighter (positive on yields)",
    "MOVE_SHIFT": "Rates volatility regime change (volatility increase lifts premia)",
    "OIL_SHOCK_UP": "Oil price shock upward (inflationary)",
    "OIL_SHOCK_DOWN": "Oil price shock downward (deflationary)",
    "MBS_CONVEXITY": "MBS hedging pressure, OAS moves, convexity effects",
    "HOUSING_TURN": "Housing market surprises: mortgage rates, starts, permits",
    "FUNDING_STRESS": "Funding stress: GC repo specials, SOFR spikes (front-end up, rest down)",
    "ECB_TONE": "European Central Bank hawkish↔dovish tone",
    "ECB_RATE_SURP": "ECB rate decision surprise",
    "BOE_TONE": "Bank of England hawkish↔dovish tone",
    "BOE_RATE_SURP": "BOE rate decision surprise",
    "YCC_JGB_SHIFT": "Bank of Japan YCC (yield curve control) tweaks, band widening",
    "CHINA_GROWTH_NEWS": "China growth news (risk-on via global growth)",
    "EU_GROWTH_NEWS": "European Union growth news",
    "GEO_EVENT": "Geopolitical events: escalations, cease-fires with clear rates linkage (risk-off)"
}

def get_openai_api_key() -> Optional[str]:
    """Load OpenAI API key from environment or config file."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return api_key
    
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                cfg = yaml.safe_load(f)
                api_key = cfg.get("openai_api_key")
                if api_key:
                    return api_key
        except Exception as e:
            print(f"[WARN] Failed to load config: {e}")
    
    return None

def call_openai_with_retry(client, messages, model, max_retries=3, **kwargs):
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
            error_str = str(e)
            # Check for rate limit errors
            if "rate_limit" in error_str.lower() or "429" in error_str:
                # Extract wait time from error if available
                import re
                wait_match = re.search(r'try again in (\d+)ms', error_str)
                if wait_match:
                    wait_seconds = int(wait_match.group(1)) / 1000.0
                    wait_seconds = min(wait_seconds + 1.0, 60.0)  # Cap at 60 seconds
                else:
                    wait_seconds = (2 ** attempt) * 2  # Longer backoff for rate limits
                
                if attempt < max_retries - 1:
                    print(f"[WARN] Rate limit hit, waiting {wait_seconds:.1f}s before retry...")
                    time.sleep(wait_seconds)
                else:
                    print(f"[ERROR] Rate limit exceeded after {max_retries} attempts")
                    return None
            else:
                print(f"[WARN] OpenAI API call failed (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return None
    return None

def extract_factors_from_article(client: OpenAI, article: Dict) -> Optional[List[Dict]]:
    """
    Uses LLM to extract economic factors from a single article.
    Returns list of {factor_name, intensity, confidence} dicts.
    """
    title = article.get("title", "")
    summary = article.get("summary", "")
    text = article.get("text", "")
    url = article.get("url", "")

    if not title and not summary and not text:
        return None

    # Limit text for prompt efficiency
    text_snippet = (text or "")[:2000]
    article_text = f"Title: {title or ''}\nSummary: {summary or ''}\nText: {text_snippet}"

    # Build factor list for prompt
    factor_list = "\n".join([f"- {f}: {FACTOR_DESCRIPTIONS.get(f, '')}" for f in ALL_FACTORS])

    prompt = f"""You are an expert fixed income strategist. Analyze this financial news article and identify which economic factors are present and their intensity.

Available factors:
{factor_list}

For each factor present in the article:
- intensity: Real number from -2.0 to +2.0 indicating direction and strength
  - Positive: factor increases yields (e.g., hawkish Fed, strong inflation)
  - Negative: factor decreases yields (e.g., dovish Fed, risk-off)
  - Magnitude: 0.5 (weak), 1.0 (moderate), 1.5 (strong), 2.0 (very strong)
- confidence: Real number from 0.0 to 1.0 indicating how confident you are this factor is present
  - 0.9-1.0: Explicitly mentioned or very clear
  - 0.7-0.9: Strongly implied
  - 0.5-0.7: Moderately implied
  - 0.3-0.5: Weakly implied
  - 0.0-0.3: Very uncertain

Article:
{article_text}

Respond with ONLY valid JSON in this exact format (no markdown, no code blocks):
{{
    "factors": [
        {{
            "factor_name": "FED_TONE",
            "intensity": 1.5,
            "confidence": 0.9,
            "reasoning": "Brief explanation"
        }},
        // ... more factors if present
    ]
}}

If no factors are present, return: {{"factors": []}}
"""

    messages = [
        {
            "role": "system",
            "content": "You are an expert fixed income strategist extracting economic factors from news. Always respond with valid JSON only, no markdown."
        },
        {"role": "user", "content": prompt}
    ]

    try:
        response = call_openai_with_retry(
            client,
            messages,
            model="gpt-4o-mini",
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        if not response:
            return None
        
        if not hasattr(response, 'choices') or not response.choices:
            return None
        
        if not response.choices[0].message:
            return None
        
        result_text = response.choices[0].message.content
        if not result_text:
            return None
        
        result_text = result_text.strip()
        if not result_text:
            return None
        
        result = json.loads(result_text)
        
        factors = result.get("factors", [])
        
        # Validate and clean factors
        cleaned_factors = []
        for f in factors:
            factor_name = f.get("factor_name")
            if factor_name in ALL_FACTORS:
                intensity = max(-2.0, min(2.0, float(f.get("intensity", 0.0))))
                confidence = max(0.0, min(1.0, float(f.get("confidence", 0.5))))
                
                if confidence > 0.3:  # Only include if confidence > 0.3
                    cleaned_factors.append({
                        "factor_name": factor_name,
                        "intensity": intensity,
                        "confidence": confidence
                    })
        
        return cleaned_factors if cleaned_factors else None
        
    except Exception as e:
        print(f"[WARN] Failed to extract factors for {url}: {e}")
        return None

def save_article_factors(article_id: int, date: str, factors: List[Dict]):
    """Save extracted factors to database."""
    conn = get_conn()
    c = conn.cursor()
    
    for factor in factors:
        c.execute("""
            INSERT INTO article_factors 
            (article_id, date, factor_name, intensity, confidence, extracted_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            article_id,
            date,
            factor["factor_name"],
            factor["intensity"],
            factor["confidence"],
            dt.datetime.now(timezone.utc).isoformat()
        ))
    
    conn.commit()
    conn.close()

def aggregate_daily_factor_scores(date: str) -> Tuple[Dict[str, float], Dict[str, int]]:
    """
    Aggregate article factors to daily factor scores.
    Formula: factor_score = sum(c * s) clipped to [-2.5, +2.5]
    Only includes factors from articles published before market close to prevent look-ahead bias.
    """
    from lookahead_bias_utils import get_market_close_time
    
    market_close = get_market_close_time(dt.datetime.strptime(date, "%Y-%m-%d").date())
    market_close_iso = market_close.isoformat()
    
    conn = get_conn()
    c = conn.cursor()
    
    # Get all factors for this date, but only from articles published before market close
    rows = c.execute("""
        SELECT af.factor_name, af.intensity, af.confidence
        FROM article_factors af
        JOIN articles a ON af.article_id = a.id
        WHERE af.date = ?
          AND (a.published_at IS NULL OR a.published_at < ?)
    """, (date, market_close_iso)).fetchall()
    
    conn.close()
    
    # Aggregate by factor
    factor_scores = {}
    factor_counts = {}
    
    for row in rows:
        factor_name = row["factor_name"]
        intensity = row["intensity"]
        confidence = row["confidence"]
        
        # Calculate contribution: c * s
        contribution = confidence * intensity
        
        if factor_name not in factor_scores:
            factor_scores[factor_name] = 0.0
            factor_counts[factor_name] = 0
        
        factor_scores[factor_name] += contribution
        factor_counts[factor_name] += 1
    
    # Clip to [-2.5, +2.5]
    for factor_name in factor_scores:
        factor_scores[factor_name] = max(-2.5, min(2.5, factor_scores[factor_name]))
    
    return factor_scores, factor_counts

def save_daily_factor_scores(date: str, factor_scores: Dict[str, float], factor_counts: Dict[str, int]):
    """Save aggregated daily factor scores to database."""
    conn = get_conn()
    c = conn.cursor()
    
    for factor_name, score in factor_scores.items():
        c.execute("""
            INSERT OR REPLACE INTO daily_factor_scores
            (date, factor_name, factor_score, total_articles, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            date,
            factor_name,
            score,
            factor_counts.get(factor_name, 0),
            dt.datetime.now(timezone.utc).isoformat()
        ))
    
    conn.commit()
    conn.close()

def extract_factors_for_date(date: str, api_key: Optional[str] = None) -> int:
    """
    Extract factors for all articles on a given date.
    Returns number of factors extracted.
    """
    if not HAS_OPENAI:
        print("[WARN] OpenAI not available. Skipping factor extraction.")
        return 0

    if not api_key:
        api_key = get_openai_api_key()
        if not api_key:
            print("[WARN] No OpenAI API key found. Skipping factor extraction.")
            return 0

    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        print(f"[ERROR] Failed to initialize OpenAI client: {e}")
        return 0

    # Get articles for this date that haven't been factor-extracted
    # Only include articles published before market close to prevent look-ahead bias
    from lookahead_bias_utils import get_market_close_time
    
    market_close = get_market_close_time(dt.datetime.strptime(date, "%Y-%m-%d").date())
    market_close_iso = market_close.isoformat()
    
    conn = get_conn()
    c = conn.cursor()
    
    articles = c.execute("""
        SELECT id, title, summary, text, url
        FROM articles
        WHERE DATE(COALESCE(published_at, fetched_at)) = DATE(?)
          AND title IS NOT NULL
          AND title != ''
          AND (published_at IS NULL OR published_at < ?)
          AND id NOT IN (
              SELECT DISTINCT article_id FROM article_factors WHERE date = ?
          )
    """, (date, market_close_iso, date)).fetchall()
    
    conn.close()
    
    if not articles:
        print(f"[INFO] No articles to extract factors from for {date}")
        # Still aggregate existing factors
        factor_scores, factor_counts = aggregate_daily_factor_scores(date)
        if factor_scores:
            save_daily_factor_scores(date, factor_scores, factor_counts)
        return 0

    print(f"[FACTOR] Extracting factors from {len(articles)} articles for {date}")

    all_factors = []
    processed = 0

    # Process articles in parallel (reduced workers to avoid rate limits)
    MAX_WORKERS = 5  # Reduced from 10 to avoid rate limits

    def extract_single(article):
        """Extract factors from a single article."""
        try:
            factors = extract_factors_from_article(client, dict(article))
            if factors:
                return (article["id"], factors, None)
            return (article["id"], [], None)
        except Exception as e:
            return (article["id"], [], str(e))

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_article = {executor.submit(extract_single, article): article for article in articles}
        
        for future in concurrent.futures.as_completed(future_to_article):
            try:
                article_id, factors, error = future.result()
                if error:
                    print(f"[WARN] Factor extraction failed for article {article_id}: {error}")
                else:
                    if factors:
                        all_factors.append((article_id, factors))
                    processed += 1
            except Exception as e:
                print(f"[WARN] Factor extraction exception: {e}")

    # Save factors
    total_factors = 0
    for article_id, factors in all_factors:
        save_article_factors(article_id, date, factors)
        total_factors += len(factors)

    # Aggregate and save daily scores
    factor_scores, factor_counts = aggregate_daily_factor_scores(date)
    if factor_scores:
        save_daily_factor_scores(date, factor_scores, factor_counts)
        print(f"[FACTOR] Aggregated {len(factor_scores)} daily factor scores for {date}")

    print(f"[FACTOR] Extracted {total_factors} factors from {processed} articles for {date}")
    return total_factors

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Extract economic factors from news articles")
    ap.add_argument("--date", type=str, help="Date (YYYY-MM-DD) to extract factors for, defaults to today")
    ap.add_argument("--days-back", type=int, default=0, help="Number of past business days to extract factors for")
    args = ap.parse_args()

    api_key = get_openai_api_key()
    if not api_key:
        print("[ERROR] No OpenAI API key found. Set OPENAI_API_KEY or add to news_config.yaml")
        return

    if args.days_back > 0:
        today = dt.date.today()
        for i in range(args.days_back):
            current_date = today - dt.timedelta(days=i)
            if current_date.weekday() < 5:  # Only process business days
                print(f"\n--- Processing factors for {current_date.isoformat()} ---")
                extract_factors_for_date(current_date.isoformat(), api_key)
    else:
        target_date = args.date if args.date else dt.date.today().isoformat()
        extract_factors_for_date(target_date, api_key)

if __name__ == "__main__":
    main()

