# Optimized News Ingestion Pipeline

This directory contains Cython-optimized versions of CPU-intensive components.

## Structure

- `optimized/` - Cython-optimized modules
- `original_python/` - Original Python scripts (for reference)

## Building

```bash
cd optimized
python3 setup.py build_ext --inplace
```

This will create `.so` (Linux/macOS) or `.pyd` (Windows) files that can be imported.

## Usage

After building, import the optimized modules:

```python
# Instead of: from extract_article import extract
from optimized.extract_article_cy import extract

# Instead of: from db import batch_insert
from optimized.db_operations_cy import get_db_ops
db = get_db_ops()
db.batch_insert_articles(articles)
```

## Performance Improvements

Expected speedups:
- **Article extraction**: 1.5-2x faster (batch operations)
- **Database operations**: 3-5x faster (batch inserts)
- **Keyword matching**: 2-3x faster (compiled regex)

## Migration

The optimized modules maintain the same API as the original Python versions, so you can drop-in replace them.

## Dependencies

- Cython >= 0.29
- NumPy (for array operations)
- Same dependencies as original (trafilatura, BeautifulSoup, etc.)

