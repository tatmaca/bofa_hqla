#!/usr/bin/env python3
"""
News Bucketing System
Categorizes news articles into 8 buckets relevant to yield curve movements:
1. Monetary Policy (Fed decisions, interest rates)
2. Economic Data (GDP, employment, inflation)
3. Geopolitical Events (wars, trade tensions, elections)
4. Market Sentiment (risk-on/risk-off, volatility)
5. Fiscal Policy (government spending, debt, deficits)
6. Credit Events (defaults, credit spreads, banking)
7. Commodity Prices (oil, gold, inflation drivers)
8. Other/General (catch-all for other news)
"""

import os
import json
import yaml
import sqlite3
import datetime as dt
from typing import List, Dict, Optional
from urllib.parse import urlparse

# Try to import OpenAI, but make it optional
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("[WARN] OpenAI not installed. Install with: pip install openai")

DB_PATH = os.environ.get("NEWS_DB_PATH", "news.db")
CONFIG_PATH = "news_config.yaml"

BUCKETS = [
    "monetary_policy",
    "economic_data",
    "geopolitical_events",
    "market_sentiment",
    "fiscal_policy",
    "credit_events",
    "commodity_prices",
    "other_general"
]

BUCKET_DESCRIPTIONS = {
    "monetary_policy": "Federal Reserve decisions, interest rate changes, quantitative easing/tightening, Fed speeches about monetary policy",
    "economic_data": "GDP reports, employment data, inflation (CPI/PCE), retail sales, manufacturing data, consumer confidence",
    "geopolitical_events": "Wars, conflicts, trade wars, elections, political instability, international tensions",
    "market_sentiment": "Risk-on/risk-off movements, market volatility (VIX), equity market movements, safe-haven flows",
    "fiscal_policy": "Government spending, budget deficits, debt ceiling, fiscal stimulus, tax policy changes",
    "credit_events": "Corporate defaults, credit spread movements, banking sector issues, credit rating changes",
    "commodity_prices": "Oil prices, gold prices, commodity inflation, supply chain disruptions affecting commodities",
    "other_general": "Other news not fitting into the above categories"
}

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_unbucketed_articles(hours: int = 24) -> List[Dict]:
    """Get articles from the last N hours that haven't been bucketed."""
    cutoff = (dt.datetime.utcnow() - dt.timedelta(hours=hours)).isoformat()
    with get_conn() as c:
        rows = c.execute("""
            SELECT id, url, title, text, summary, source, published_at, status
            FROM articles
            WHERE (bucket IS NULL OR bucket = '')
              AND COALESCE(published_at, fetched_at) >= ?
            ORDER BY COALESCE(published_at, fetched_at) DESC
        """, (cutoff,)).fetchall()
    return [dict(row) for row in rows]

def bucket_with_llm(article: Dict, api_key: Optional[str] = None) -> tuple:
    """
    Use LLM to bucket a single article.
    Returns (bucket_name, confidence_score)
    """
    if not HAS_OPENAI:
        return ("other_general", 0.5)
    
    if api_key:
        openai.api_key = api_key
    elif os.environ.get("OPENAI_API_KEY"):
        openai.api_key = os.environ.get("OPENAI_API_KEY")
    else:
        print("[WARN] No OpenAI API key found. Using fallback bucketing.")
        return bucket_with_keywords(article)
    
    # Prepare article text
    text_parts = []
    if article.get("title"):
        text_parts.append(f"Title: {article['title']}")
    if article.get("summary"):
        text_parts.append(f"Summary: {article['summary']}")
    if article.get("text"):
        # Limit text length to avoid token limits
        text = article["text"][:2000] if len(article.get("text", "")) > 2000 else article.get("text", "")
        text_parts.append(f"Text: {text}")
    
    article_text = "\n\n".join(text_parts)
    
    # Build prompt
    bucket_list = "\n".join([f"- {b}: {BUCKET_DESCRIPTIONS[b]}" for b in BUCKETS])
    prompt = f"""Categorize the following news article into ONE of these 8 buckets that best describes its impact on U.S. Treasury yield curves:

{bucket_list}

Article:
{article_text}

Respond with ONLY a JSON object in this exact format:
{{"bucket": "bucket_name", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Use cheaper model for bucketing
            messages=[
                {"role": "system", "content": "You are a financial news categorizer. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        result_text = response.choices[0].message.content.strip()
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(result_text)
        bucket = result.get("bucket", "other_general")
        confidence = float(result.get("confidence", 0.5))
        
        # Validate bucket
        if bucket not in BUCKETS:
            bucket = "other_general"
        
        return (bucket, confidence)
        
    except Exception as e:
        print(f"[WARN] LLM bucketing failed for article {article.get('id')}: {e}")
        return bucket_with_keywords(article)

def bucket_with_keywords(article: Dict) -> tuple:
    """Fallback keyword-based bucketing."""
    text = f"{article.get('title', '')} {article.get('summary', '')} {article.get('text', '')}".lower()
    
    keywords = {
        "monetary_policy": ["fed", "federal reserve", "interest rate", "monetary policy", "quantitative easing", "qe", "qt", "fomc"],
        "economic_data": ["gdp", "employment", "unemployment", "inflation", "cpi", "pce", "retail sales", "manufacturing", "consumer confidence"],
        "geopolitical_events": ["war", "conflict", "trade war", "election", "sanctions", "geopolitical"],
        "market_sentiment": ["volatility", "vix", "risk-on", "risk-off", "safe haven", "market sentiment"],
        "fiscal_policy": ["budget", "deficit", "debt ceiling", "fiscal", "government spending", "stimulus"],
        "credit_events": ["default", "credit spread", "banking", "credit rating", "corporate bond"],
        "commodity_prices": ["oil", "crude", "gold", "commodity", "commodities", "supply chain"]
    }
    
    scores = {}
    for bucket, kw_list in keywords.items():
        score = sum(1 for kw in kw_list if kw in text)
        scores[bucket] = score
    
    if max(scores.values()) > 0:
        best_bucket = max(scores.items(), key=lambda x: x[1])[0]
        confidence = min(0.7, scores[best_bucket] / 3.0)  # Cap confidence for keyword matching
    else:
        best_bucket = "other_general"
        confidence = 0.3
    
    return (best_bucket, confidence)

def update_article_bucket(article_id: int, bucket: str, confidence: float):
    """Update article with bucket assignment."""
    with get_conn() as c:
        c.execute("""
            UPDATE articles
            SET bucket = ?, bucket_confidence = ?
            WHERE id = ?
        """, (bucket, confidence, article_id))

def bucket_articles(hours: int = 24, batch_size: int = 50, api_key: Optional[str] = None):
    """Bucket all unbucketed articles from the last N hours."""
    articles = get_unbucketed_articles(hours)
    print(f"[BUCKET] Found {len(articles)} unbucketed articles")
    
    if not articles:
        return
    
    # Load config for API key if not provided
    if not api_key and os.path.exists(CONFIG_PATH):
        cfg = yaml.safe_load(open(CONFIG_PATH))
        api_key = cfg.get("openai_api_key") or os.environ.get("OPENAI_API_KEY")
    
    processed = 0
    for i, article in enumerate(articles):
        if i >= batch_size:
            print(f"[BUCKET] Processed {batch_size} articles (stopping at batch limit)")
            break
        
        bucket, confidence = bucket_with_llm(article, api_key)
        update_article_bucket(article["id"], bucket, confidence)
        processed += 1
        
        if (i + 1) % 10 == 0:
            print(f"[BUCKET] Processed {i + 1}/{min(len(articles), batch_size)} articles")
    
    print(f"[BUCKET] Completed: {processed} articles bucketed")

def get_bucket_counts(date: Optional[str] = None) -> Dict[str, int]:
    """Get article counts per bucket for a given date (or today)."""
    if date is None:
        date = dt.date.today().isoformat()
    
    with get_conn() as c:
        rows = c.execute("""
            SELECT bucket, COUNT(*) as count
            FROM articles
            WHERE DATE(COALESCE(published_at, fetched_at)) = DATE(?)
              AND bucket IS NOT NULL
            GROUP BY bucket
        """, (date,)).fetchall()
    
    return {row["bucket"]: row["count"] for row in rows}

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Bucket news articles")
    ap.add_argument("--hours", type=int, default=24, help="Hours to look back")
    ap.add_argument("--batch-size", type=int, default=50, help="Max articles to process")
    ap.add_argument("--api-key", type=str, help="OpenAI API key")
    args = ap.parse_args()
    
    bucket_articles(hours=args.hours, batch_size=args.batch_size, api_key=args.api_key)

