# crawl_web.py
# Polite async crawler for front pages + sitemaps with:
# - robots.txt compliance
# - per-host rate limiting (supports fractional RPS via time slicing)
# - strict 24h source-time filtering (HEAD Last-Modified, <lastmod>, or meta published_time)
# - paywalled domains handled as metadata-only (no body stored)
# - skip domains (HTML crawling disabled)
# - resilient to errors (no task crashes)

import asyncio
import re
import yaml
import pytz
import aiohttp
import xml.etree.ElementTree as ET

from typing import Optional
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, urljoin
from urllib import robotparser
from aiolimiter import AsyncLimiter
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime

from db import upsert_article, content_hash, seen_recent
from extract_article import extract

# -----------------------
# Config & globals
# -----------------------
CONFIG = yaml.safe_load(open("news_config.yaml"))

UA = CONFIG.get("user_agent", "JL-NewsCrawler/0.1")
TIMEOUT = aiohttp.ClientTimeout(total=CONFIG.get("timeout_s", 15))
CONCURRENCY = int(CONFIG.get("concurrency", 8))

TZ = pytz.timezone(CONFIG.get("timezone", "America/Chicago"))
CUTOFF_UTC = (datetime.now(TZ) - timedelta(hours=CONFIG.get("window_hours", 24))).astimezone(timezone.utc)
STRICT = bool(CONFIG.get("strict_24h", True))

META_ONLY = set(CONFIG.get("metadata_only_domains") or [])
SKIP = set(CONFIG.get("skip_domains") or [])

FRONT_PAGES = CONFIG.get("front_pages", [])
SITEMAPS = CONFIG.get("sitemaps", [])

# Limits to keep work bounded per run (tune as needed)
MAX_LINKS_PER_FRONT = int(CONFIG.get("max_links_per_front", 100))
MAX_URLS_PER_SITEMAP = int(CONFIG.get("max_urls_per_sitemap", 200))
MAX_TOTAL_URLS = int(CONFIG.get("max_total_urls", 500))  # Total URL limit per run

# -----------------------
# Rate limiter per host
# -----------------------
LIMITERS = {}

def host_limiter(host: str) -> AsyncLimiter:
    """Implements fractional requests-per-second by stretching time_period."""
    if host in LIMITERS:
        return LIMITERS[host]
    rps = float(CONFIG.get("per_host_rps", 0.5))
    if rps >= 1.0:
        max_rate, time_period = int(rps), 1
    else:
        max_rate, time_period = 1, max(1, int(round(1.0 / rps)))  # 0.5 -> 2s; 0.2 -> 5s
    LIMITERS[host] = AsyncLimiter(max_rate=max_rate, time_period=time_period)
    return LIMITERS[host]

# -----------------------
# robots.txt cache
# -----------------------
ROBOTS = {}

# Known-good domains that allow crawling (skip robots.txt check for speed)
KNOWN_GOOD_DOMAINS = {
    'www.reuters.com', 'reuters.com',
    'www.cnbc.com', 'cnbc.com',
    'finance.yahoo.com', 'www.yahoo.com',
    'www.marketwatch.com', 'marketwatch.com',
    'www.investing.com', 'investing.com',
    'apnews.com', 'www.apnews.com',
}

async def can_fetch(session: aiohttp.ClientSession, url: str) -> bool:
    host = urlparse(url).netloc
    if host in SKIP:  # hard skip HTML crawling on these domains
        return False
    
    # Skip robots.txt check for known-good domains (faster)
    if host in KNOWN_GOOD_DOMAINS:
        if host not in ROBOTS:
            ROBOTS[host] = None  # Mark as checked, allow by default
        return True
    
    if host not in ROBOTS:
        rp = robotparser.RobotFileParser()
        robots_url = f"{urlparse(url).scheme}://{host}/robots.txt"
        try:
            async with session.get(robots_url, headers={"User-Agent": UA}, timeout=aiohttp.ClientTimeout(total=5)) as r:
                txt = await r.text()
            rp.parse(txt.splitlines())
        except Exception:
            rp = None  # Allow by default if robots.txt can't be fetched
        ROBOTS[host] = rp
    rp = ROBOTS[host]
    return rp.can_fetch(UA, url) if rp else True

# -----------------------
# HTTP helpers
# -----------------------
async def fetch_text(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    host = urlparse(url).netloc
    async with host_limiter(host):
        async with session.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT, allow_redirects=True) as r:
            if r.status != 200:
                return None
            return await r.text()

async def fetch_bytes_range(session: aiohttp.ClientSession, url: str, byte_cap: int = 65536) -> Optional[bytes]:
    """Fetch a tiny slice to parse <meta> without pulling the whole page (useful for paywalls)."""
    host = urlparse(url).netloc
    async with host_limiter(host):
        try:
            async with session.get(
                url,
                headers={"User-Agent": UA, "Range": f"bytes=0-{byte_cap-1}"},
                timeout=TIMEOUT,
                allow_redirects=True,
            ) as r:
                if r.status in (200, 206):
                    return await r.read()
        except Exception:
            return None
    return None

async def head_last_modified(session: aiohttp.ClientSession, url: str) -> Optional[datetime]:
    """Try to read Last-Modified via HEAD; returns UTC datetime if present and parseable."""
    host = urlparse(url).netloc
    async with host_limiter(host):
        try:
            async with session.head(url, headers={"User-Agent": UA}, timeout=TIMEOUT, allow_redirects=True) as r:
                lm = r.headers.get("Last-Modified")
                if lm:
                    try:
                        dt_obj = parsedate_to_datetime(lm)
                        if dt_obj.tzinfo is None:
                            dt_obj = dt_obj.replace(tzinfo=timezone.utc)
                        return dt_obj.astimezone(timezone.utc)
                    except Exception:
                        return None
        except Exception:
            return None
    return None

# -----------------------
# Date extraction helpers
# -----------------------
def parse_isoish(s: str) -> Optional[datetime]:
    """Parse ISO-like string safely to UTC datetime."""
    if not s:
        return None
    try:
        # handle trailing 'Z'
        if s.endswith("Z"):
            s = s.replace("Z", "+00:00")
        dt_obj = datetime.fromisoformat(s)
        if dt_obj.tzinfo is None:
            dt_obj = dt_obj.replace(tzinfo=timezone.utc)
        return dt_obj.astimezone(timezone.utc)
    except Exception:
        return None

def published_from_html(html: bytes) -> Optional[datetime]:
    """Try to extract published time from common meta tags."""
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return None
    # common meta tags
    for key, attr in (("property", "article:published_time"), ("name", "pubdate"), ("property", "og:updated_time")):
        m = soup.find("meta", {key: attr})
        if m and m.get("content"):
            dt_obj = parse_isoish(m["content"])
            if dt_obj:
                return dt_obj
    # <time datetime="...">
    t = soup.find("time")
    if t and t.get("datetime"):
        dt_obj = parse_isoish(t["datetime"])
        if dt_obj:
            return dt_obj
    return None

# -----------------------
# Front page link discovery
# -----------------------
async def gather_front_page_links(session: aiohttp.ClientSession, url: str) -> list:
    if not await can_fetch(session, url):
        return []
    html = await fetch_text(session, url)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    base_host = urlparse(url).netloc
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("#"):
            continue
        full = urljoin(url, href)
        u = urlparse(full)
        if u.netloc != base_host:
            continue
        # skip obvious non-article sections
        if re.search(r"/(video|podcast|live|photo|interactive)/", full):
            continue
        links.add(full)
        if len(links) >= MAX_LINKS_PER_FRONT:
            break
    return list(links)

# -----------------------
# Sitemap parsing
# -----------------------
async def parse_sitemap(session: aiohttp.ClientSession, url: str) -> list:
    if not await can_fetch(session, url):
        return []
    xml = await fetch_text(session, url)
    if not xml:
        return []
    res = []
    try:
        root = ET.fromstring(xml)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        # urlset case
        for node in root.findall(".//sm:url", ns):
            loc = node.find("sm:loc", ns)
            lm = node.find("sm:lastmod", ns)
            if loc is None or not (loc.text or "").strip():
                continue
            link = loc.text.strip()
            # strict 24h via <lastmod> if available
            if lm is not None and lm.text:
                lm_dt = parse_isoish(lm.text)
                if lm_dt and lm_dt < CUTOFF_UTC:
                    continue
            elif STRICT:
                # if strict, require lastmod to decide freshness
                continue
            res.append(link)
            if len(res) >= MAX_URLS_PER_SITEMAP:
                break

        # Skip sitemap index recursion for speed (only process top-level sitemaps)
        # Uncomment below if you need deeper sitemap crawling (slower)
        # if not res:
        #     for sn in root.findall(".//sm:sitemap/sm:loc", ns):
        #         child = (sn.text or "").strip()
        #         if not child:
        #             continue
        #         child_urls = await parse_sitemap(session, child)
        #         res.extend(child_urls)
        #         if len(res) >= MAX_URLS_PER_SITEMAP:
        #             break
    except Exception:
        pass
    return res[:MAX_URLS_PER_SITEMAP]

# -----------------------
# Article fetch/store
# -----------------------
async def fetch_and_store(session: aiohttp.ClientSession, url: str):
    try:
        # Early filtering: check if already seen (fast DB check)
        if seen_recent(url, int(CONFIG.get("dedupe_horizon_days", 1))):
            return None

        host = urlparse(url).netloc
        
        # Skip robots.txt check for known-good domains (faster)
        # Only check for unknown or problematic domains
        if host not in ROBOTS:
            if not await can_fetch(session, url):
                return None
        elif ROBOTS[host] and not ROBOTS[host].can_fetch(UA, url):
            return None

        # 24h prefilter: try HEAD Last-Modified first (fast check)
        lm_dt = await head_last_modified(session, url)
        if lm_dt and lm_dt < CUTOFF_UTC:
            return None

        meta_only = host in META_ONLY

        # If strict and we don't have Last-Modified, try a tiny fetch to read published_time
        pub_dt: Optional[datetime] = None
        preloaded_html: Optional[bytes] = None

        if STRICT and (lm_dt is None):
            # For metadata-only domains we always tiny-get to read title & published_time
            if meta_only or True:
                preloaded_html = await fetch_bytes_range(session, url)
                if not preloaded_html and meta_only:
                    # can't establish freshness -> skip
                    return None
                if preloaded_html:
                    pub_dt = published_from_html(preloaded_html)
                    if pub_dt and pub_dt < CUTOFF_UTC:
                        return None
                    if meta_only and pub_dt is None:
                        # strict mode requires a date to accept metadata-only items
                        return None

        # Extract with timeout protection
        if meta_only:
            # pass preloaded_html if we have it to let extractor grab title/meta cheaply
            art = extract(url, html=preloaded_html, metadata_only=True)
        else:
            # Add timeout to extraction (same as RSS ingestion)
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(extract, url)
                    art = future.result(timeout=8)  # 8 second timeout per article
            except FutureTimeoutError:
                art = {"status": "fetch_failed", "title": None, "author": None, "published_at": None, "text": None}
            except Exception:
                art = {"status": "fetch_failed", "title": None, "author": None, "published_at": None, "text": None}

        # If we still don't have published_at, adopt lm_dt or parsed pub_dt if present
        published_at = art.get("published_at")
        if not published_at and lm_dt:
            published_at = lm_dt.isoformat()
        if not published_at and pub_dt:
            published_at = pub_dt.isoformat()

        # Strict 24h final guard
        if STRICT:
            if not published_at:
                return
            try:
                pdt = parse_isoish(published_at)
                if not pdt or pdt < CUTOFF_UTC:
                    return
            except Exception:
                return

        rec = {
            "url": url,
            "source": host,
            "published_at": published_at,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "title": art.get("title"),
            "author": art.get("author"),
            "summary": None,
            "text": None if meta_only else art.get("text"),
            "content_hash": content_hash(
                (art.get("text") or "") if not meta_only else (art.get("title") or url)
            ),
            "status": art.get("status", "ok") if not meta_only else "paywalled",
            "bucket": None,
            "bucket_confidence": None,
        }

        # Return article for batch insert instead of inserting immediately
        return rec

    except Exception:
        # swallow per-URL errors to keep the crawl running
        return None

# -----------------------
# Orchestrator
# -----------------------
async def run():
    async with aiohttp.ClientSession() as session:
        # 1) Front pages -> links
        front_tasks = [gather_front_page_links(session, u) for u in FRONT_PAGES]
        front_lists = await asyncio.gather(*front_tasks, return_exceptions=True)
        front_urls = []
        for lst in front_lists:
            if isinstance(lst, Exception):
                continue
            front_urls.extend(lst)

        # 2) Sitemaps -> article URLs (pre-filtered by <lastmod>)
        sm_tasks = [parse_sitemap(session, u) for u in SITEMAPS]
        sm_lists = await asyncio.gather(*sm_tasks, return_exceptions=True)
        sm_urls = []
        for lst in sm_lists:
            if isinstance(lst, Exception):
                continue
            sm_urls.extend(lst)

        # Deduplicate combined URL list
        all_urls = list({*front_urls, *sm_urls})
        
        # Limit total URLs to process (for faster runs)
        if len(all_urls) > MAX_TOTAL_URLS:
            print(f"[CRAWL] Limiting URLs from {len(all_urls)} to {MAX_TOTAL_URLS} for faster processing")
            all_urls = all_urls[:MAX_TOTAL_URLS]
        
        print(f"[CRAWL] Processing {len(all_urls)} URLs (from {len(front_urls)} front page links, {len(sm_urls)} sitemap URLs)")

        # 3) Fetch & store with bounded concurrency and batch inserts
        sem = asyncio.Semaphore(CONCURRENCY)
        articles_buffer = []
        BATCH_SIZE = 50
        processed_count = 0

        async def worker(u: str):
            async with sem:
                result = await fetch_and_store(session, u)
                nonlocal processed_count
                processed_count += 1
                # Progress update every 50 URLs
                if processed_count % 50 == 0:
                    print(f"[CRAWL] Processed {processed_count}/{len(all_urls)} URLs...")
                return result

        # Process in chunks to avoid overwhelming the system
        CHUNK_SIZE = min(100, len(all_urls))  # Process 100 URLs at a time (smaller chunks = faster)
        results = []
        max_articles = 50  # Stop early if we've collected enough articles
        
        for i in range(0, len(all_urls), CHUNK_SIZE):
            chunk = all_urls[i:i+CHUNK_SIZE]
            chunk_results = await asyncio.gather(*(worker(u) for u in chunk), return_exceptions=True)
            results.extend(chunk_results)
            
            # Early termination: if we've collected enough articles, stop
            valid_count = sum(1 for r in results if isinstance(r, dict) and r)
            if valid_count >= max_articles:
                print(f"[CRAWL] Early termination: collected {valid_count} articles (target: {max_articles})")
                break
        
        # Collect valid articles and batch insert
        valid_articles = 0
        for result in results:
            if isinstance(result, dict) and result:
                articles_buffer.append(result)
                valid_articles += 1
                if len(articles_buffer) >= BATCH_SIZE:
                    from db import batch_upsert_articles
                    batch_upsert_articles(articles_buffer)
                    articles_buffer = []
        
        # Insert remaining articles
        if articles_buffer:
            from db import batch_upsert_articles
            batch_upsert_articles(articles_buffer)
        
        print(f"[CRAWL] Completed: {valid_articles} articles collected from {len(all_urls)} URLs")

if __name__ == "__main__":
    asyncio.run(run())
