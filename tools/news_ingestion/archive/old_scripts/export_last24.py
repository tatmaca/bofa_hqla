# export_last24.py
import os
import csv
import sqlite3
import yaml
import pytz
from datetime import datetime, timedelta, timezone

DB_PATH = os.environ.get("NEWS_DB_PATH", "news.db")
CONFIG_PATH = "news_config.yaml"

def utc_cutoff_from_config(cfg):
    tzname = cfg.get("timezone", "America/Chicago")
    window_hours = int(cfg.get("window_hours", 24))
    tz = pytz.timezone(tzname)
    now_local = datetime.now(tz)
    cutoff_utc = (now_local - timedelta(hours=window_hours)).astimezone(timezone.utc)
    return cutoff_utc

def write_csv(rows, out_path):
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = None
        for idx, r in enumerate(rows):
            if w is None:
                w = csv.writer(f)
                w.writerow(r.keys())  # header
            w.writerow([r[k] for k in r.keys()])
        if w is None:
            # write header even if empty; match expected columns
            header = ["url","source","published_at","fetched_at","title","author","summary","text","status"]
            csv.writer(f).writerow(header)

def main():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Missing {CONFIG_PATH}")

    cfg = yaml.safe_load(open(CONFIG_PATH))
    cutoff_utc = utc_cutoff_from_config(cfg).isoformat()

    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row

        # Content set: usable text for modeling
        content_rows = c.execute(
            """
            SELECT url, source, published_at, fetched_at, title, author, summary, text, status
            FROM articles
            WHERE COALESCE(published_at, fetched_at) >= ?
              AND status = 'ok'
              AND text IS NOT NULL
            ORDER BY COALESCE(published_at, fetched_at) DESC
            """,
            (cutoff_utc,),
        ).fetchall()

        # Metadata set: paywalled/metadata-only (no body text)
        meta_rows = c.execute(
            """
            SELECT url, source, published_at, fetched_at, title, author, summary, text, status
            FROM articles
            WHERE COALESCE(published_at, fetched_at) >= ?
              AND (status != 'ok' OR text IS NULL)
            ORDER BY COALESCE(published_at, fetched_at) DESC
            """,
            (cutoff_utc,),
        ).fetchall()

    write_csv(content_rows, "news_last24_content.csv")
    write_csv(meta_rows, "news_last24_metadata.csv")

    print(f"[export_last24] cutoff_utc: {cutoff_utc}")
    print(f"[export_last24] content rows:   {len(content_rows)}  -> news_last24_content.csv")
    print(f"[export_last24] metadata rows:  {len(meta_rows)}     -> news_last24_metadata.csv")
    print("[export_last24] done.")

if __name__ == "__main__":
    main()
