import sqlite3, hashlib, os, datetime as dt
from datetime import timezone
from pathlib import Path

# Get database path - use absolute path relative to this script's directory
_script_dir = Path(__file__).parent
_default_db_path = _script_dir / "news.db"
DB_PATH = os.environ.get("NEWS_DB_PATH", str(_default_db_path))

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as c, open("schema.sql","r") as f:
        c.executescript(f.read())

def upsert_article(rec):
    """Insert or update a single article (for backward compatibility)."""
    batch_upsert_articles([rec])

def batch_upsert_articles(articles):
    """Batch insert/update articles - much faster than individual inserts."""
    if not articles:
        return
    
    # Filter out articles with null or empty titles
    articles = [rec for rec in articles if rec.get("title") and rec.get("title").strip()]
    
    if not articles:
        return
    
    fields = ("url","source","published_at","fetched_at","title","author","summary","text","content_hash","status","bucket","bucket_confidence")
    
    # Prepare batch data
    values = []
    for rec in articles:
        vals = tuple(rec.get(k) for k in fields)
        values.append(vals)
    
    sql = f"""
    INSERT INTO articles({",".join(fields)})
    VALUES ({",".join(["?"]*len(fields))})
    ON CONFLICT(url) DO UPDATE SET
      source=excluded.source,
      published_at=excluded.published_at,
      fetched_at=excluded.fetched_at,
      title=excluded.title,
      author=excluded.author,
      summary=excluded.summary,
      text=excluded.text,
      content_hash=excluded.content_hash,
      status=excluded.status,
      bucket=excluded.bucket,
      bucket_confidence=excluded.bucket_confidence
    """
    with get_conn() as c:
        c.executemany(sql, values)
        c.commit()

def content_hash(text:str)->str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

def seen_recent(url:str, days:int=7)->bool:
    with get_conn() as c:
        row = c.execute("SELECT fetched_at FROM articles WHERE url=?",(url,)).fetchone()
    if not row: return False
    try:
        fetched = dt.datetime.fromisoformat(row["fetched_at"])
        return (dt.datetime.now(timezone.utc) - fetched).days < days
    except: return True

def start_ingestion_run(run_date: str = None):
    """Start tracking a daily ingestion run."""
    if run_date is None:
        run_date = dt.date.today().isoformat()
    started_at = dt.datetime.now(timezone.utc).isoformat()
    with get_conn() as c:
        c.execute("""
            INSERT OR IGNORE INTO ingestion_runs (run_date, started_at, status)
            VALUES (?, ?, 'running')
        """, (run_date, started_at))
    return run_date

def complete_ingestion_run(run_date: str, rss_processed: int = 0, rss_skipped: int = 0,
                           crawl_processed: int = 0, crawl_skipped: int = 0,
                           status: str = "completed", error_message: str = None):
    """Complete tracking a daily ingestion run."""
    completed_at = dt.datetime.now(timezone.utc).isoformat()
    # Count new articles added today
    with get_conn() as c:
        new_count = c.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE DATE(fetched_at) = DATE(?)
        """, (completed_at,)).fetchone()[0]
        
        c.execute("""
            UPDATE ingestion_runs
            SET completed_at = ?, rss_processed = ?, rss_skipped = ?,
                crawl_processed = ?, crawl_skipped = ?, total_new_articles = ?,
                status = ?, error_message = ?
            WHERE run_date = ?
        """, (completed_at, rss_processed, rss_skipped, crawl_processed, 
              crawl_skipped, new_count, status, error_message, run_date))
    return new_count

def get_last_run_date():
    """Get the date of the last successful ingestion run."""
    with get_conn() as c:
        row = c.execute("""
            SELECT run_date FROM ingestion_runs 
            WHERE status = 'completed' 
            ORDER BY run_date DESC LIMIT 1
        """).fetchone()
    return row["run_date"] if row else None
