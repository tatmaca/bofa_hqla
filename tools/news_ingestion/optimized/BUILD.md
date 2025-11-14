# Building Optimized Components

## Quick Start

```bash
cd optimized
pip install -r requirements.txt
python3 setup.py build_ext --inplace
```

## What Gets Built

- `extract_article_cy.cpython-*.so` - Optimized article extractor
- `db_operations_cy.cpython-*.so` - Optimized database operations
- `text_processing_cy.cpython-*.so` - Optimized text processing

## Using Optimized Components

After building, you can use the optimized versions:

```python
# Option 1: Use optimized extractor
try:
    from optimized.extract_article_cy import extract
except ImportError:
    # Fallback to original
    from extract_article import extract

# Option 2: Use optimized DB operations
try:
    from optimized.db_operations_cy import get_db_ops
    db = get_db_ops("news.db")
    db.batch_insert_articles(articles)  # Much faster!
except ImportError:
    # Fallback to original
    from db import get_conn
    # ... use original methods
```

## Performance Testing

```bash
python3 benchmark.py  # Compare original vs optimized
```

## Troubleshooting

**ImportError after building:**
- Make sure you're in the `optimized/` directory or add it to PYTHONPATH
- Check that `.so` files were created: `ls -la *.so`

**Build errors:**
- Make sure Cython is installed: `pip install cython`
- Make sure you have a C compiler (gcc/clang)
- On macOS: `xcode-select --install`

## Fallback

If building fails, the pipeline will automatically fall back to original Python implementations.

