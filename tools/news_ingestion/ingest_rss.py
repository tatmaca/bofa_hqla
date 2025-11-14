import feedparser, yaml, datetime as dt, pytz, os
from datetime import timezone
import asyncio
import concurrent.futures
from urllib.parse import urlparse
from db import upsert_article, content_hash, seen_recent
from extract_article import extract

CONFIG = yaml.safe_load(open("news_config.yaml"))
DEDAYS = CONFIG.get("dedupe_horizon_days", 1)
META_ONLY = set(CONFIG.get("metadata_only_domains") or [])
SKIP = set(CONFIG.get("skip_domains") or [])
MAX_WORKERS = CONFIG.get("rss_max_workers", 4)  # Parallel RSS feed parsing

def normalize_time(entry):
    for fld in ("published_parsed", "updated_parsed"):
        ts = getattr(entry, fld, None)
        if ts:
            try:
                return dt.datetime(*ts[:6], tzinfo=dt.timezone.utc).isoformat()
            except:
                pass
    return None

def process_entry(e, cutoff_utc, strict):
    """Process a single RSS entry."""
    url = getattr(e, "link", None)
    if not url or seen_recent(url, DEDAYS):
        return None

    src = urlparse(url).netloc
    if src in SKIP:
        return None

    published = normalize_time(e)
    if not published and strict:
        return None  # enforce 24h at source stage
    if published:
        try:
            pub_dt = dt.datetime.fromisoformat(published)
            if pub_dt < cutoff_utc:
                return None
        except:
            if strict:
                return None

    meta_only = src in META_ONLY

    if meta_only:
        art = {"status": "paywalled", "title": getattr(e, "title", None),
               "author": None, "published_at": published, "text": None}
    else:
        try:
            art = extract(url)
        except Exception:
            art = {"status": "fetch_failed", "title": getattr(e, "title", None),
                   "author": None, "published_at": published, "text": None}

    # Use historical end of day UTC if set, otherwise current time
    fetched_at_str = os.getenv("_HISTORICAL_END_OF_DAY_UTC")
    if fetched_at_str:
        fetched_at = dt.datetime.fromisoformat(fetched_at_str)
    else:
        fetched_at = dt.datetime.now(timezone.utc)
    
    # Ensure published_at is not after target date (if in historical mode)
    published_dt = None
    if published:
        try:
            published_dt = dt.datetime.fromisoformat(published)
        except:
            pass
    
    if published_dt and fetched_at_str:
        # Historical mode: ensure no future articles
        end_of_day_utc = dt.datetime.fromisoformat(fetched_at_str)
        if published_dt > end_of_day_utc:
            return None  # Reject articles published after target date
    
    rec = {
        "url": url,
        "source": src,
        "published_at": published or art.get("published_at"),
        "fetched_at": fetched_at.isoformat(),
        "title": art.get("title") or getattr(e, "title", None),
        "author": art.get("author"),
        "summary": getattr(e, "summary", None),
        "text": None if meta_only else art.get("text"),
        "content_hash": content_hash(
            (art.get("text") or "") if not meta_only else (getattr(e, "title", "") or "")
        ),
        "status": art.get("status", "ok") if not meta_only else "paywalled",
        "bucket": None,
        "bucket_confidence": None,
    }
    # Don't insert here - return for batch insert
    return rec

def process_feed(feed_url):
    """Process a single RSS feed and return entries."""
    try:
        f = feedparser.parse(feed_url, agent=CONFIG["user_agent"])
        return f.entries
    except Exception as e:
        print(f"[WARN] Failed to parse feed {feed_url}: {e}")
        return []

def run(target_date: dt.date = None):
    """Run RSS ingestion. If target_date is provided, only collect articles published on or before that date."""
    tz = pytz.timezone(CONFIG.get("timezone", "America/Chicago"))
    
    # Support historical dates via environment variable or parameter
    if target_date is None:
        target_date_str = os.getenv("TARGET_DATE")
        if target_date_str:
            target_date = dt.datetime.strptime(target_date_str, "%Y-%m-%d").date()
    
    if target_date:
        # Historical mode: end of target date
        end_of_day_local = dt.datetime.combine(target_date, dt.time(23, 59, 59))
        end_of_day_local = tz.localize(end_of_day_local)
        end_of_day_utc = end_of_day_local.astimezone(dt.timezone.utc)
        cutoff_utc = end_of_day_utc - dt.timedelta(hours=CONFIG.get("window_hours", 24))
        # Store for use in process_entry
        os.environ["_HISTORICAL_END_OF_DAY_UTC"] = end_of_day_utc.isoformat()
    else:
        # Current mode
        cutoff_utc = (dt.datetime.now(tz) - dt.timedelta(hours=CONFIG.get("window_hours", 24))).astimezone(dt.timezone.utc)
        end_of_day_utc = dt.datetime.now(dt.timezone.utc)
    
    strict = CONFIG.get("strict_24h", True)

    # Parallel RSS feed parsing
    all_entries = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_feed = {executor.submit(process_feed, feed): feed for feed in CONFIG["rss_feeds"]}
        for future in concurrent.futures.as_completed(future_to_feed):
            feed_url = future_to_feed[future]
            try:
                entries = future.result()
                all_entries.extend(entries)
                print(f"[OK] Processed RSS feed: {feed_url} ({len(entries)} entries)")
            except Exception as e:
                print(f"[ERROR] Feed {feed_url} failed: {e}")

    # Process entries with parallel extraction (for non-paywalled)
    # Collect articles in batches for efficient database operations
    articles_buffer = []
    BATCH_SIZE = 50  # Insert in batches of 50
    processed = 0
    skipped = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONFIG.get("concurrency", 12)) as executor:
        future_to_entry = {
            executor.submit(process_entry, e, cutoff_utc, strict): e 
            for e in all_entries
        }
        for future in concurrent.futures.as_completed(future_to_entry):
            try:
                result = future.result()
                if result:
                    articles_buffer.append(result)
                    processed += 1
                    # Batch insert when buffer is full
                    if len(articles_buffer) >= BATCH_SIZE:
                        from db import batch_upsert_articles
                        batch_upsert_articles(articles_buffer)
                        articles_buffer = []
                else:
                    skipped += 1
            except Exception as e:
                skipped += 1
                print(f"[WARN] Entry processing failed: {e}")
    
    # Insert remaining articles
    if articles_buffer:
        from db import batch_upsert_articles
        batch_upsert_articles(articles_buffer)
    
    print(f"[RSS] Processed: {processed}, Skipped: {skipped}")

if __name__ == "__main__":
    run()
