# Performance Optimization Guide

## Current Bottlenecks

1. **Article Extraction** - CPU-bound HTML parsing
2. **Database Operations** - Individual inserts are slow
3. **Text Processing** - Keyword matching on large text
4. **Network I/O** - Already optimized with async, but can batch better

## Optimization Strategy

### 1. Cython for CPU-Bound Operations

**Targets:**
- Article extraction (HTML parsing)
- Text processing (keyword matching)
- Database batch operations

**Expected Speedup:** 2-5x for CPU-bound tasks

### 2. Batch Operations

**Current:** Individual database inserts
**Optimized:** Batch inserts (10-100x faster)

**Current:** One-by-one article processing
**Optimized:** Process in batches

### 3. Compiled Regex

**Current:** Re-compile regex patterns each time
**Optimized:** Pre-compile and reuse

## Implementation Status

- [x] Cython setup structure
- [x] Fast extractor (extract_article_cy.pyx)
- [x] Fast DB operations (db_operations_cy.pyx)
- [x] Fast keyword matcher (text_processing_cy.pyx)
- [ ] Build script
- [ ] Integration with main pipeline
- [ ] Performance benchmarks

## Building

```bash
cd optimized
pip install cython numpy
python3 setup.py build_ext --inplace
```

## Testing

```bash
# Benchmark original vs optimized
python3 benchmark.py
```

## Notes

- Network I/O is already optimized with async/await
- Most gains will come from batch operations
- Cython helps with CPU-bound text processing
- Database batch inserts provide biggest speedup

