# News Ingestion Pipeline Optimization

## Overview

Created optimized versions of CPU-intensive components using Cython, while keeping original Python scripts for reference.

## Structure

```
tools/news_ingestion/
├── optimized/              # Cython-optimized modules
│   ├── extract_article_cy.pyx
│   ├── db_operations_cy.pyx
│   ├── text_processing_cy.pyx
│   ├── setup.py
│   └── run_ingest_optimized.py
├── original_python/        # Original scripts (reference)
│   ├── extract_article.py
│   ├── db.py
│   └── bucket_news.py
└── [existing files]        # Current working pipeline
```

## Optimizations Implemented

### 1. Batch Database Operations
- **Before:** Individual INSERT statements (slow)
- **After:** Batch INSERT with `executemany()` (10-100x faster)
- **File:** `optimized/db_operations_cy.pyx`

### 2. Compiled Text Processing
- **Before:** Re-compile regex on each call
- **After:** Pre-compiled regex patterns (2-3x faster)
- **File:** `optimized/text_processing_cy.pyx`

### 3. Optimized Article Extraction
- **Before:** Python-level HTML parsing
- **After:** Cython-optimized with type hints (1.5-2x faster)
- **File:** `optimized/extract_article_cy.pyx`

### 4. Improved Async Handling
- **Before:** Sequential processing
- **After:** Better batching and async coordination
- **File:** `optimized/run_ingest_optimized.py`

## Expected Performance Gains

| Component | Speedup | Notes |
|-----------|---------|-------|
| Database inserts | 10-100x | Batch operations |
| Keyword matching | 2-3x | Compiled regex |
| Article extraction | 1.5-2x | Cython optimization |
| Overall pipeline | 2-5x | Combined improvements |

## Building

```bash
cd tools/news_ingestion/optimized
pip install cython numpy
python3 setup.py build_ext --inplace
```

## Usage

### Option 1: Use Optimized Pipeline

```bash
cd tools/news_ingestion
python3 optimized/run_ingest_optimized.py
```

### Option 2: Import Optimized Modules

```python
# In your scripts, try optimized first, fallback to original
try:
    from optimized.extract_article_cy import extract
    from optimized.db_operations_cy import get_db_ops
except ImportError:
    from extract_article import extract
    from db import get_conn
```

## Current Status

- [OK] Cython modules created
- [OK] Batch operations implemented
- [OK] Original scripts backed up
- ⏳ Build and test (requires Cython installation)
- ⏳ Integration with main pipeline

## Notes

- **I/O Bound Operations:** Network requests are already optimized with async/await
- **Biggest Gains:** Batch database operations provide the most speedup
- **Backward Compatible:** Original Python scripts still work
- **Fallback:** Pipeline automatically falls back to Python if Cython modules unavailable

## Next Steps

1. Build Cython modules: `cd optimized && python3 setup.py build_ext --inplace`
2. Test performance: Compare original vs optimized
3. Integrate: Update main pipeline to use optimized versions
4. Monitor: Check for any compatibility issues

