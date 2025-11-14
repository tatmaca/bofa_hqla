# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False

"""
Optimized text processing for keyword matching
Original Python version kept in ../original_python/bucket_news.py
"""

cimport cython
from libc.string cimport strstr, tolower
from cpython.string cimport PyString_AsString
from cpython.unicode cimport PyUnicode_AsUTF8String

import re
from typing import Dict, Tuple

# Keyword patterns for each bucket - compiled once
cdef dict KEYWORD_PATTERNS = {
    "monetary_policy": re.compile(
        r'\b(fed|federal reserve|interest rate|quantitative easing|qt|qe|'
        r'fomc|jerome powell|monetary policy|rate hike|rate cut)\b',
        re.IGNORECASE
    ),
    "economic_data": re.compile(
        r'\b(gdp|unemployment|inflation|cpi|pce|retail sales|'
        r'manufacturing|consumer confidence|employment data)\b',
        re.IGNORECASE
    ),
    "geopolitical_events": re.compile(
        r'\b(war|conflict|trade war|election|political|geopolitical|'
        r'tension|sanctions|diplomatic)\b',
        re.IGNORECASE
    ),
    "market_sentiment": re.compile(
        r'\b(risk-on|risk-off|volatility|vix|safe-haven|market sentiment|'
        r'equity market|stock market)\b',
        re.IGNORECASE
    ),
    "fiscal_policy": re.compile(
        r'\b(fiscal|government spending|budget deficit|debt ceiling|'
        r'fiscal stimulus|tax policy)\b',
        re.IGNORECASE
    ),
    "credit_events": re.compile(
        r'\b(default|credit spread|banking|credit rating|corporate debt|'
        r'credit event)\b',
        re.IGNORECASE
    ),
    "commodity_prices": re.compile(
        r'\b(oil|gold|commodity|crude|supply chain|commodity inflation)\b',
        re.IGNORECASE
    ),
}

cdef class FastKeywordMatcher:
    """Fast keyword-based bucketing using compiled regex"""
    
    @cython.boundscheck(False)
    @cython.wraparound(False)
    cpdef tuple match_keywords(self, str text, str title = None):
        """Fast keyword matching - returns (bucket, confidence)"""
        cdef str combined_text
        cdef str bucket
        cdef object pattern
        cdef int max_matches = 0
        cdef str best_bucket = "other_general"
        cdef int matches
        
        if not text:
            text = ""
        if title:
            combined_text = f"{title} {text}"
        else:
            combined_text = text
        
        # Find bucket with most keyword matches
        for bucket, pattern in KEYWORD_PATTERNS.items():
            matches = len(pattern.findall(combined_text))
            if matches > max_matches:
                max_matches = matches
                best_bucket = bucket
        
        # Confidence based on match count
        cdef float confidence = min(0.9, 0.5 + (max_matches * 0.1))
        
        return (best_bucket, confidence)

# Global instance
_matcher = None

def bucket_with_keywords_fast(article: Dict) -> Tuple[str, float]:
    """Public API - fast keyword bucketing"""
    global _matcher
    if _matcher is None:
        _matcher = FastKeywordMatcher()
    
    text = article.get("text", "") or ""
    title = article.get("title", "") or ""
    
    return _matcher.match_keywords(text, title)

