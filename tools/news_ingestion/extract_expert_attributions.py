#!/usr/bin/env python3
"""
Extract Expert Attributions from News Articles
Uses LLM to identify expert opinions on which news contributed to yield curve changes.
"""

import os
import json
import yaml
import datetime as dt
from datetime import timezone
from typing import Dict, List, Optional
from pathlib import Path

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from db import get_conn
from lookahead_bias_utils import get_market_close_time

CONFIG_PATH = Path(__file__).parent / "news_config.yaml"

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

def extract_attributions_from_articles(date: str, articles: List[Dict], 
                                      yield_changes: Dict) -> List[Dict]:
    """
    Extract expert attributions from articles using LLM.
    
    Args:
        date: Date of yield changes
        articles: List of article dicts with title, text, summary
        yield_changes: Dict with actual yield changes (delta_2y, delta_5y, etc.)
    
    Returns:
        List of attribution dicts
    """
    if not HAS_OPENAI:
        return []
    
    api_key = get_openai_api_key()
    if not api_key:
        return []
    
    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        print(f"[ERROR] Failed to initialize OpenAI client: {e}")
        return []
    
    attributions = []
    
    # Process articles in batches
    batch_size = 10
    for i in range(0, len(articles), batch_size):
        batch = articles[i:i+batch_size]
        
        # Prepare prompt with yield changes context
        yield_context = f"""
YIELD CURVE CHANGES on {date}:
- 2y: {yield_changes.get('delta_2y', 0.0):+.2f} bps
- 5y: {yield_changes.get('delta_5y', 0.0):+.2f} bps
- 10y: {yield_changes.get('delta_10y', 0.0):+.2f} bps
- 30y: {yield_changes.get('delta_30y', 0.0):+.2f} bps
- 2s10s: {yield_changes.get('delta_2s10s', 0.0):+.2f} bps
- 2s30s: {yield_changes.get('delta_2s30s', 0.0):+.2f} bps
"""
        
        articles_text = []
        for art in batch:
            title = art.get('title', '')
            summary = art.get('summary', '')
            text = art.get('text', '')[:500] if art.get('text') else ''  # Limit text length
            source = art.get('source', '')
            
            art_text = f"Title: {title}\nSource: {source}\n"
            if summary:
                art_text += f"Summary: {summary}\n"
            if text:
                art_text += f"Text: {text[:500]}...\n"
            articles_text.append(art_text)
        
        prompt = f"""You are analyzing financial news articles to identify expert opinions on which news events contributed to yield curve movements.

{yield_context}

ARTICLES:
{chr(10).join(f'{i+1}. {art}' for i, art in enumerate(articles_text))}

TASK: For each article, identify if it contains expert opinions (from analysts, strategists, traders, etc.) that attribute yield curve changes to specific news events. Look for:
- Direct quotes from experts
- Analyst commentary
- Market strategist opinions
- Trader statements
- Attribution statements like "yields moved due to...", "the curve steepened because...", etc.

For each article with expert attribution, extract:
1. The attribution statement/quote
2. Which yield changes it attributes (2y, 5y, 10y, 30y, spreads)
3. Confidence level (0.0-1.0)

Respond with ONLY valid JSON in this format:
{{
    "attributions": [
        {{
            "article_index": <0-based index>,
            "attribution_text": "<exact quote or paraphrased attribution>",
            "attributed_yields": ["2y", "10y"],  // which yields are mentioned
            "confidence": 0.85,
            "expert_name": "<name if mentioned>",
            "expert_title": "<title if mentioned>"
        }}
    ]
}}

If no attributions found, return: {{"attributions": []}}
"""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a financial news analyst extracting expert opinions on yield curve movements. Always respond with valid JSON only."
                },
                {"role": "user", "content": prompt}
            ]
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            result = json.loads(result_text)
            
            # Process attributions
            for attr in result.get("attributions", []):
                article_idx = attr.get("article_index", 0)
                if 0 <= article_idx < len(batch):
                    article = batch[article_idx]
                    attributions.append({
                        "article_id": article.get("id"),
                        "article_url": article.get("url"),
                        "attribution_text": attr.get("attribution_text", ""),
                        "attributed_yields": attr.get("attributed_yields", []),
                        "confidence": attr.get("confidence", 0.5),
                        "expert_name": attr.get("expert_name", ""),
                        "expert_title": attr.get("expert_title", ""),
                        "source": article.get("source", ""),
                        "date": date
                    })
        
        except Exception as e:
            print(f"[WARN] Failed to extract attributions from batch: {e}")
            continue
    
    return attributions

def save_attributions(attributions: List[Dict]):
    """Save expert attributions to database."""
    if not attributions:
        return
    
    conn = get_conn()
    c = conn.cursor()
    
    for attr in attributions:
        c.execute("""
            INSERT INTO expert_attributions
            (date, article_id, article_url, attribution_text, source, extracted_at, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            attr["date"],
            attr.get("article_id"),
            attr.get("article_url"),
            attr["attribution_text"],
            attr.get("source", ""),
            dt.datetime.now(timezone.utc).isoformat(),
            attr.get("confidence", 0.5),
            dt.datetime.now(timezone.utc).isoformat()
        ))
    
    conn.commit()
    conn.close()
    print(f"[ATTRIB] Saved {len(attributions)} expert attributions")

def extract_attributions_for_date(date: str) -> int:
    """
    Extract expert attributions for a given date.
    
    Returns:
        Number of attributions extracted
    """
    # Get yield changes for the date
    conn = get_conn()
    c = conn.cursor()
    
    row = c.execute("""
        SELECT delta_zeros_pct, delta_spreads_pct
        FROM yield_curve_daily
        WHERE date = ?
    """, (date,)).fetchone()
    
    if not row:
        print(f"[WARN] No yield curve data for {date}")
        conn.close()
        return 0
    
    try:
        delta_zeros = json.loads(row["delta_zeros_pct"])
        delta_spreads = json.loads(row["delta_spreads_pct"])
    except:
        conn.close()
        return 0
    
    yield_changes = {
        "delta_2y": delta_zeros.get("2y", 0.0) * 100,  # Convert to bps
        "delta_5y": delta_zeros.get("5y", 0.0) * 100,
        "delta_10y": delta_zeros.get("10y", 0.0) * 100,
        "delta_30y": delta_zeros.get("30y", 0.0) * 100,
        "delta_2s10s": delta_spreads.get("2s10s", 0.0) * 100,
        "delta_2s30s": delta_spreads.get("2s30s", 0.0) * 100,
    }
    
    # Get articles published before market close on this date
    from lookahead_bias_utils import get_market_close_time, is_article_before_market_close
    
    market_close = get_market_close_time(dt.datetime.strptime(date, "%Y-%m-%d").date())
    market_close_iso = market_close.isoformat()
    
    # Get articles for this date that were published before market close
    rows = c.execute("""
        SELECT id, url, title, text, summary, source, published_at
        FROM articles
        WHERE DATE(COALESCE(published_at, fetched_at)) = DATE(?)
        AND published_at IS NOT NULL
        AND published_at < ?
        AND title IS NOT NULL
        AND title != ''
        ORDER BY published_at DESC
        LIMIT 100
    """, (date, market_close_iso)).fetchall()
    
    conn.close()
    
    if not rows:
        print(f"[INFO] No articles found for {date} (before market close)")
        return 0
    
    articles = [dict(row) for row in rows]
    print(f"[ATTRIB] Extracting attributions from {len(articles)} articles for {date}")
    
    attributions = extract_attributions_from_articles(date, articles, yield_changes)
    save_attributions(attributions)
    
    return len(attributions)

def main():
    import argparse
    
    ap = argparse.ArgumentParser(description="Extract expert attributions from news")
    ap.add_argument("--date", type=str, help="Date (YYYY-MM-DD), defaults to today")
    ap.add_argument("--days-back", type=int, default=0, help="Process last N days")
    args = ap.parse_args()
    
    if args.date:
        dates = [args.date]
    elif args.days_back > 0:
        today = dt.date.today()
        dates = [(today - dt.timedelta(days=i)).isoformat() for i in range(args.days_back)]
    else:
        dates = [dt.date.today().isoformat()]
    
    total = 0
    for date in dates:
        count = extract_attributions_for_date(date)
        total += count
    
    print(f"\n[ATTRIB] Total attributions extracted: {total}")

if __name__ == "__main__":
    main()

