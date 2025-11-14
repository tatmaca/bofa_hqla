# News Ingestion Improvements

## Current Status

**Collection Rate:** 3-23 articles/day (average ~10-15)
**Sources:** 4 RSS feeds, 3 front pages, 2 sitemaps
**Rate Limit:** 0.5 RPS (very conservative)

## Identified Issues

1. **Limited RSS Feeds** - Only 4 feeds
2. **Conservative Rate Limiting** - 0.5 RPS (1 request every 2 seconds)
3. **Strict Date Filtering** - Drops articles without published dates
4. **Limited Front Pages** - Only 3 sources
5. **Limited Sitemaps** - Only 2 sources
6. **Low Limits** - 200 links/front, 500 URLs/sitemap

## Proposed Improvements

### 1. Add More RSS Feeds (4 → 15+ feeds)

**New Sources:**
- Reuters: Added business and markets feeds
- AP News: Added business and financial markets feeds
- CNBC: Added top news and markets feeds
- Bloomberg: Added main feed
- Yahoo Finance: Added news feed
- MarketWatch: Re-enabled (was skipped)
- Zero Hedge: Financial news aggregator
- Investing.com: Financial news

**Expected Impact:** +200-300% more articles

### 2. Increase Rate Limits

- **Current:** 0.5 RPS (1 request every 2 seconds)
- **Enhanced:** 1.0 RPS (1 request per second)
- **Still polite:** 1 RPS is well within acceptable limits

**Expected Impact:** 2x faster collection

### 3. Relax Strict Date Filtering

- **Current:** `strict_24h: true` - Drops articles without dates
- **Enhanced:** `strict_24h: false` - Collects all articles, filter later

**Expected Impact:** +20-30% more articles

### 4. Add More Front Pages (3 → 8 pages)

**New Sources:**
- Reuters business section
- CNBC business section
- Yahoo Finance
- MarketWatch
- Investing.com

**Expected Impact:** +50-100% more articles

### 5. Add More Sitemaps (2 → 4 sitemaps)

**New Sources:**
- CNBC sitemap
- Yahoo Finance sitemap

**Expected Impact:** +30-50% more articles

### 6. Increase Collection Limits

- **Max Links Per Front:** 200 → 300
- **Max URLs Per Sitemap:** 500 → 1000

**Expected Impact:** +50% more articles from crawling

### 7. Increase Concurrency

- **Current:** 8 concurrent workers
- **Enhanced:** 12 concurrent workers

**Expected Impact:** Faster collection, more articles processed

## Expected Results

**Before:**
- 3-23 articles/day (average ~10-15)
- 4 RSS feeds
- Conservative rate limiting

**After:**
- 30-60+ articles/day (estimated)
- 15+ RSS feeds
- Faster, more efficient collection
- More diverse sources

## Implementation

1. **Backup current config:**
   ```bash
   cp news_config.yaml news_config.yaml.backup
   ```

2. **Apply enhanced config:**
   ```bash
   cp news_config_enhanced.yaml news_config.yaml
   ```

3. **Test the changes:**
   ```bash
   python3 run_ingest.py
   ```

4. **Monitor results:**
   ```bash
   python3 check_status.py
   ```

## Notes

- **Rate Limiting:** 1.0 RPS is still very polite and should not cause issues
- **Strict Filtering:** Can always filter by date in post-processing
- **Paywalls:** Many sources are metadata-only (title/URL), which is still useful
- **Deduplication:** System already handles duplicate URLs

## Rollback

If issues occur, restore the backup:
```bash
cp news_config.yaml.backup news_config.yaml
```

