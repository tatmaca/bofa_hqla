# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False

"""
Optimized article extraction using Cython
Original Python version kept in ../original_python/extract_article.py
"""

from libc.string cimport strlen, strstr
from libc.stdlib cimport malloc, free
cimport cython
from cpython.string cimport PyString_AsString, PyString_FromString
from cpython.unicode cimport PyUnicode_AsUTF8String

import trafilatura
from bs4 import BeautifulSoup
from dateutil import parser as dtparse
from typing import Optional
import datetime as dt

cdef class FastExtractor:
    """Optimized article extractor using Cython"""
    
    @cython.boundscheck(False)
    @cython.wraparound(False)
    cpdef dict extract(self, str url, bytes html = None, bint metadata_only = False):
        """Extract article content - optimized version"""
        cdef dict result
        
        if metadata_only:
            if html is None:
                return {"status": "paywalled", "title": None, "author": None, 
                       "published_at": None, "text": None}
            
            # Fast metadata extraction
            soup = BeautifulSoup(html, "html.parser")
            title = soup.title.string.strip() if soup.title else None
            pub = None
            
            # Fast meta tag search
            m = soup.find("meta", {"property": "article:published_time"}) or \
                soup.find("meta", {"name": "pubdate"})
            
            if m and m.get("content"):
                try:
                    pub = dtparse.parse(m["content"]).astimezone(dt.timezone.utc).isoformat()
                except:
                    pass
            
            return {"status": "paywalled", "title": title, "author": None, 
                   "published_at": pub, "text": None}
        
        # Full extraction
        downloaded = html or trafilatura.fetch_url(url)
        if not downloaded:
            return {"status": "fetch_failed"}
        
        # Use trafilatura for extraction (already optimized C library)
        data = trafilatura.extract(downloaded, url=url, include_formatting=False,
                                  include_links=False, favor_recall=True, with_metadata=True)
        if not data:
            return {"status": "extract_failed"}
        
        meta = trafilatura.bare_extraction(downloaded, url=url) or {}
        title = meta.get("title")
        author = meta.get("author")
        date = meta.get("date")
        
        if date:
            try:
                date = dtparse.parse(date).astimezone(dt.timezone.utc).isoformat()
            except:
                pass
        
        return {"title": title, "author": author, "published_at": date, 
               "text": data, "status": "ok"}

# Global instance for reuse
_extractor = None

def extract(url: str, html: Optional[bytes] = None, *, metadata_only: bool = False):
    """Public API - same interface as original"""
    global _extractor
    if _extractor is None:
        _extractor = FastExtractor()
    return _extractor.extract(url, html, metadata_only)

