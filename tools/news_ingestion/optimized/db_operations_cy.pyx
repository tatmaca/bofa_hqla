# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False

"""
Optimized database operations using Cython
Original Python version kept in ../original_python/db.py
"""

cimport cython
from libc.string cimport strcmp
from cpython.list cimport PyList_Append, PyList_New
from cpython.dict cimport PyDict_New, PyDict_SetItem

import sqlite3
from typing import List, Dict, Optional
import json

cdef class FastDBOps:
    """Optimized database operations"""
    
    cdef str db_path
    cdef object _conn_cache
    
    def __init__(self, str db_path = "news.db"):
        self.db_path = db_path
        self._conn_cache = None
    
    cdef object _get_conn(self):
        """Get or create connection with caching"""
        if self._conn_cache is None:
            self._conn_cache = sqlite3.connect(self.db_path)
            self._conn_cache.row_factory = sqlite3.Row
        return self._conn_cache
    
    @cython.boundscheck(False)
    cpdef void batch_insert_articles(self, list articles):
        """Batch insert articles - much faster than individual inserts"""
        cdef object conn = self._get_conn()
        cdef object cursor = conn.cursor()
        cdef dict article
        cdef list values_list = []
        
        # Prepare batch insert
        for article in articles:
            values_list.append((
                article.get("url"),
                article.get("source"),
                article.get("published_at"),
                article.get("fetched_at"),
                article.get("title"),
                article.get("author"),
                article.get("summary"),
                article.get("text"),
                article.get("content_hash"),
                article.get("status")
            ))
        
        # Single batch insert
        cursor.executemany("""
            INSERT OR IGNORE INTO articles 
            (url, source, published_at, fetched_at, title, author, summary, text, content_hash, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values_list)
        
        conn.commit()
    
    @cython.boundscheck(False)
    cpdef void batch_update_buckets(self, list updates):
        """Batch update article buckets"""
        cdef object conn = self._get_conn()
        cdef object cursor = conn.cursor()
        cdef dict update
        
        # Prepare batch update
        values_list = [(u["bucket"], u["confidence"], u["id"]) for u in updates]
        
        cursor.executemany("""
            UPDATE articles
            SET bucket = ?, bucket_confidence = ?
            WHERE id = ?
        """, values_list)
        
        conn.commit()
    
    @cython.boundscheck(False)
    cpdef list get_unbucketed_fast(self, str cutoff):
        """Fast query for unbucketed articles"""
        cdef object conn = self._get_conn()
        cdef object cursor = conn.cursor()
        
        rows = cursor.execute("""
            SELECT id, url, title, text, summary, source, published_at, status
            FROM articles
            WHERE (bucket IS NULL OR bucket = '')
              AND COALESCE(published_at, fetched_at) >= ?
            ORDER BY COALESCE(published_at, fetched_at) DESC
        """, (cutoff,)).fetchall()
        
        return [dict(row) for row in rows]

# Global instance
_db_ops = None

def get_db_ops(db_path: str = "news.db"):
    """Get global DB operations instance"""
    global _db_ops
    if _db_ops is None:
        _db_ops = FastDBOps(db_path)
    return _db_ops

