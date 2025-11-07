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
import time
from datetime import timezone
from typing import List, Dict, Optional
from urllib.parse import urlparse

# Try to import OpenAI, but make it optional
try:
    from openai import OpenAI
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
    cutoff = (dt.datetime.now(timezone.utc) - dt.timedelta(hours=hours)).isoformat()
    with get_conn() as c:
        rows = c.execute("""
            SELECT id, url, title, text, summary, source, published_at, status
            FROM articles
            WHERE (bucket IS NULL OR bucket = '')
              AND COALESCE(published_at, fetched_at) >= ?
            ORDER BY COALESCE(published_at, fetched_at) DESC
        """, (cutoff,)).fetchall()
    return [dict(row) for row in rows]

def call_openai_bucket(client, messages, max_retries=2, **kwargs):
    """Call OpenAI API for bucketing with retry logic."""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                messages=messages,
                **kwargs
            )
            return response
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 1 + attempt  # Short backoff for bucketing
                error_msg = str(e).lower()
                if "rate limit" in error_msg:
                    wait_time = min(wait_time * 2, 10)
                time.sleep(wait_time)
            else:
                raise
    return None

def bucket_with_llm(article: Dict, api_key: Optional[str] = None, client: Optional[object] = None) -> tuple:
    """
    Use LLM to bucket a single article.
    Returns (bucket_name, confidence_score)
    """
    if not HAS_OPENAI:
        return ("other_general", 0.5)
    
    # Use provided client or create new one
    if client is None:
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key and os.path.exists(CONFIG_PATH):
            cfg = yaml.safe_load(open(CONFIG_PATH))
            api_key = cfg.get("openai_api_key")
        
        if not api_key:
            return bucket_with_keywords(article)
        
        client = OpenAI(api_key=api_key)
    
    # Prepare article text - prioritize title and summary
    text_parts = []
    if article.get("title"):
        text_parts.append(f"Title: {article['title']}")
    if article.get("summary"):
        summary = article["summary"][:300] if len(article.get("summary", "")) > 300 else article.get("summary", "")
        text_parts.append(f"Summary: {summary}")
    if article.get("text"):
        # Use first 1500 chars of text (most important info usually at start)
        text = article["text"][:1500] if len(article.get("text", "")) > 1500 else article.get("text", "")
        text_parts.append(f"Text: {text}")
    
    article_text = "\n\n".join(text_parts)
    
    # Build improved prompt with examples
    bucket_list = "\n".join([f"{i+1}. {b}: {BUCKET_DESCRIPTIONS[b]}" for i, b in enumerate(BUCKETS)])
    prompt = f"""Categorize this financial news article into ONE of these 8 categories based on its potential impact on U.S. Treasury yield curves:

{bucket_list}

Article:
{article_text}

Consider:
- Which category BEST describes the primary driver of yield curve movement?
- Monetary policy news affects short-end (2y) most
- Economic data affects intermediate tenors (5y, 10y)
- Geopolitical events often cause flight-to-quality (yields down)
- Fiscal policy affects long-end (30y) most
- If unclear or multiple categories fit, choose the most impactful one

Respond with ONLY valid JSON (no markdown):
{{"bucket": "exact_bucket_name", "confidence": 0.0-1.0, "reasoning": "one sentence why"}}
"""

    try:
        messages = [
            {
                "role": "system",
                "content": "You are a financial news analyst specializing in fixed income markets. Categorize articles accurately. Always respond with valid JSON only, no markdown."
            },
            {"role": "user", "content": prompt}
        ]
        
        response = call_openai_bucket(
            client,
            messages,
            model="gpt-4o-mini",
            temperature=0.2,  # Lower temperature for more consistent categorization
            max_tokens=150,
            response_format={"type": "json_object"}  # Force JSON output
        )
        
        if not response:
            return bucket_with_keywords(article)
        
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse JSON directly
        try:
            result = json.loads(result_text)
        except json.JSONDecodeError:
            # Try extracting from markdown
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            result = json.loads(result_text)
        
        bucket = result.get("bucket", "other_general")
        confidence = float(result.get("confidence", 0.5))
        
        # Validate bucket name
        if bucket not in BUCKETS:
            # Try fuzzy match
            bucket_lower = bucket.lower()
            for valid_bucket in BUCKETS:
                if valid_bucket.lower() in bucket_lower or bucket_lower in valid_bucket.lower():
                    bucket = valid_bucket
                    break
            else:
                bucket = "other_general"
                confidence = min(confidence, 0.5)  # Lower confidence if invalid bucket
        
        # Clamp confidence
        confidence = max(0.0, min(1.0, confidence))
        
        return (bucket, confidence)
        
    except Exception as e:
        # Silent fallback for individual article failures
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
    
    # Initialize OpenAI client once for reuse
    client = None
    if HAS_OPENAI and api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
        except Exception as e:
            print(f"[WARN] Failed to initialize OpenAI client: {e}")
    
    processed = 0
    errors = 0
    for i, article in enumerate(articles):
        if i >= batch_size:
            print(f"[BUCKET] Processed {batch_size} articles (stopping at batch limit)")
            break
        
        try:
            bucket, confidence = bucket_with_llm(article, api_key, client)
            update_article_bucket(article["id"], bucket, confidence)
            processed += 1
        except Exception as e:
            errors += 1
            # Fallback to keyword bucketing on error
            bucket, confidence = bucket_with_keywords(article)
            update_article_bucket(article["id"], bucket, confidence)
            processed += 1
        
        # Progress update every 10 articles
        if (i + 1) % 10 == 0:
            print(f"[BUCKET] Processed {i + 1}/{min(len(articles), batch_size)} articles" + 
                  (f" ({errors} errors)" if errors > 0 else ""))
        
        # Small delay to avoid rate limits
        if client and (i + 1) % 20 == 0:
            time.sleep(0.5)
    
    print(f"[BUCKET] Completed: {processed} articles bucketed" + 
          (f" ({errors} fell back to keyword matching)" if errors > 0 else ""))

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

