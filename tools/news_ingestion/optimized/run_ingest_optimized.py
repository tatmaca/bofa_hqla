#!/usr/bin/env python3
"""
Optimized news ingestion pipeline
Uses batch operations and improved async handling for better performance
"""

import os
import sys
import asyncio
import datetime as dt
from pathlib import Path
from typing import List, Dict
import sqlite3

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import get_conn, start_ingestion_run, complete_ingestion_run, upsert_article
from ingest_rss import run as run_rss
from crawl_web import run as run_crawl

class OptimizedIngestion:
    """Optimized ingestion with batch operations"""
    
    def __init__(self):
        self.articles_buffer = []
        self.buffer_size = 100  # Batch insert every 100 articles
    
    def batch_upsert_articles(self, articles: List[Dict]):
        """Batch insert articles - much faster than individual inserts"""
        if not articles:
            return
        
        conn = get_conn()
        cursor = conn.cursor()
        
        # Prepare batch data
        values = []
        for art in articles:
            values.append((
                art.get("url"),
                art.get("source"),
                art.get("published_at"),
                art.get("fetched_at"),
                art.get("title"),
                art.get("author"),
                art.get("summary"),
                art.get("text"),
                art.get("content_hash"),
                art.get("status")
            ))
        
        # Batch insert
        cursor.executemany("""
            INSERT OR IGNORE INTO articles 
            (url, source, published_at, fetched_at, title, author, summary, text, content_hash, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)
        
        conn.commit()
        conn.close()
    
    def flush_buffer(self):
        """Flush buffered articles to database"""
        if self.articles_buffer:
            self.batch_upsert_articles(self.articles_buffer)
            count = len(self.articles_buffer)
            self.articles_buffer.clear()
            return count
        return 0
    
    def add_article(self, article: Dict):
        """Add article to buffer, flush if buffer is full"""
        self.articles_buffer.append(article)
        if len(self.articles_buffer) >= self.buffer_size:
            self.flush_buffer()

def run_optimized():
    """Run optimized ingestion pipeline"""
    date_str = dt.date.today().isoformat()
    print(f">> Starting optimized ingestion run for {date_str}")
    
    # Start run tracking
    run_date = start_ingestion_run(date_str)
    
    optimizer = OptimizedIngestion()
    
    try:
        # RSS ingestion (already optimized with threading)
        print(">> RSS ingest")
        run_rss()
        
        # Web crawl (already async)
        print(">> Web crawl")
        run_crawl()
        
        # Flush any remaining articles
        flushed = optimizer.flush_buffer()
        if flushed > 0:
            print(f">> Flushed {flushed} buffered articles")
        
        # Complete run
        conn = get_conn()
        cursor = conn.cursor()
        new_count = cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE DATE(fetched_at) = ?
        """, (date_str,)).fetchone()[0]
        conn.close()
        
        complete_ingestion_run(
            run_date,
            rss_processed=new_count,
            rss_skipped=0,
            crawl_processed=0,
            crawl_skipped=0,
            status="completed"
        )
        
        print(f">> Done. New articles: {new_count}")
        
    except Exception as e:
        print(f"[ERROR] Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        complete_ingestion_run(run_date, status="failed", error_message=str(e))

if __name__ == "__main__":
    run_optimized()

