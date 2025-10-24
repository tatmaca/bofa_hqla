#!/usr/bin/env python3
"""
daily_monitor_dag.py (extended)
Sources:
  - Fed RSS (press + speeches)
  - Treasury FiscalData auctions_query (near-term issuance)
  - Federal Register (Fed/OCC/FDIC)
  - OCC RSS (news releases)
  - FDIC RSS (press releases)
  - SEC RSS (press releases) [optional]
  - Finnhub Economic Calendar [optional; requires FINNHUB_API_KEY + finnhub-python]
  - Trading Economics Calendar [optional; requires TE_API_CLIENT, TE_API_KEY + tradingeconomics]

Behavior:
  - Optional sources fail "soft" (no crash) if packages/keys are missing or no rows.
  - All outputs are appended into DuckDB tables.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import duckdb
import pandas as pd
from dateutil import parser as dateparser
from prefect import flow, task, get_run_logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

import httpx
import feedparser


# -----------------------------
# Feeds / APIs
# -----------------------------
FED_RSS_FEEDS = [
    "https://www.federalreserve.gov/feeds/press_all.xml",
    "https://www.federalreserve.gov/feeds/speeches.xml",
]

# OCC / FDIC / SEC RSS
OCC_RSS = "https://www.occ.gov/rss/occ-news-releases.xml"
FDIC_RSS = "https://www.fdic.gov/rss/press-releases.xml"
SEC_RSS  = "https://www.sec.gov/news/pressreleases.rss"  # optional; may rate-limit

# Treasury FiscalData
FISCALDATA_BASE = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
TREASURY_AUCTIONS_ENDPOINT = "v1/accounting/od/auctions_query"

# Federal Register
FEDERAL_REGISTER_API = "https://www.federalregister.gov/api/v1/documents.json"


# -----------------------------
# Exceptions / utils
# -----------------------------
class ExpectedEmpty(Exception):
    """Raised when a source legitimately yields no rows or is intentionally skipped."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_utc(ts: Any) -> Optional[datetime]:
    if ts is None:
        return None
    try:
        dt = dateparser.parse(str(ts))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def upsert_df(con: duckdb.DuckDBPyConnection, df: pd.DataFrame, table: str) -> None:
    if df.empty:
        return
    cols = ", ".join([f'"{c}"' for c in df.columns])
    tmp_view = f"tmp_{table}_{int(_utcnow().timestamp())}"
    con.register(tmp_view, df)
    con.execute(f"CREATE TABLE IF NOT EXISTS {table} AS SELECT * FROM {tmp_view} WHERE 1=0;")
    con.execute(f'INSERT INTO {table} SELECT {cols} FROM {tmp_view};')
    con.unregister(tmp_view)


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=1, max=10),
    retry=retry_if_exception_type(httpx.HTTPError),
)
def _get_json(url: str, params: Dict[str, Any] | None = None, timeout: int = 20) -> Dict[str, Any]:
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        r = client.get(url, params=params)
        r.raise_for_status()
        return r.json()


# -----------------------------
# Tasks: Core
# -----------------------------
@task
def fetch_fed_rss(feeds: List[str]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for feed_url in feeds:
        parsed = feedparser.parse(feed_url)
        for e in parsed.entries:
            rows.append(
                {
                    "source": "fed_rss",
                    "feed": feed_url,
                    "title": e.get("title"),
                    "published_utc": to_utc(e.get("published") or e.get("updated")),
                    "url": e.get("link"),
                    "summary": e.get("summary"),
                    "retrieved_utc": _utcnow(),
                }
            )
    df = pd.DataFrame(rows).drop_duplicates(subset=["url", "title"]).reset_index(drop=True)
    if df.empty:
        raise ExpectedEmpty("No Fed items today")
    return df


@task
def fetch_treasury_upcoming_auctions(as_of_date: datetime) -> pd.DataFrame:
    since = (as_of_date - timedelta(days=7)).date().isoformat()
    params = {
        "format": "json",
        "page[number]": 1,
        "page[size]": 10000,
        "filter": f"auction_date:gte:{since}",
        "sort": "-auction_date",
    }
    url = f"{FISCALDATA_BASE}/{TREASURY_AUCTIONS_ENDPOINT}"
    try:
        data = _get_json(url, params=params)
    except httpx.HTTPStatusError as e:
        if e.response is not None and e.response.status_code == 404:
            raise ExpectedEmpty("auctions_query 404 (treat as empty)")
        raise

    items = data.get("data") or []
    if not items:
        raise ExpectedEmpty("No auctions in window")

    rows: List[Dict[str, Any]] = []
    for it in items:
        attrs = it.get("attributes", {})
        rows.append(
            {
                "source": "treasury_fiscaldata",
                "security_type": attrs.get("security_type"),
                "security_term": attrs.get("security_term"),
                "security_term_no": attrs.get("security_term_no"),
                "security_term_unit": attrs.get("security_term_unit"),
                "cusip": attrs.get("cusip"),
                "announcement_date": attrs.get("announcement_date"),
                "auction_date": attrs.get("auction_date"),
                "issue_date": attrs.get("issue_date"),
                "offering_amount": pd.to_numeric(attrs.get("offering_amount"), errors="coerce"),
                "total_accepted": pd.to_numeric(attrs.get("total_accepted"), errors="coerce"),
                "record_date": attrs.get("record_date"),
                "retrieved_utc": _utcnow(),
            }
        )
    df = pd.DataFrame(rows)
    for c in ["announcement_date", "auction_date", "issue_date", "record_date"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce", utc=True)
    return df.sort_values("auction_date", ascending=False).reset_index(drop=True)


@task
def fetch_federal_register_docs(as_of_date: datetime, per_page: int = 200) -> pd.DataFrame:
    since = (as_of_date - timedelta(days=7)).date().isoformat()
    params = {
        "per_page": per_page,
        "order": "newest",
        "conditions[publication_date][gte]": since,
        "conditions[agencies]": [
            "federal-reserve-system",
            "comptroller-of-the-currency",
            "federal-deposit-insurance-corporation",
        ],
        "fields[]": [
            "title",
            "publication_date",
            "start_page",
            "end_page",
            "type",
            "document_number",
            "html_url",
            "agencies",
        ],
    }
    data = _get_json(FEDERAL_REGISTER_API, params=params)
    results = data.get("results", [])
    if not results:
        raise ExpectedEmpty("No FR docs")
    rows: List[Dict[str, Any]] = []
    for r in results:
        ags = ", ".join([a.get("name", "") for a in r.get("agencies", [])])
        rows.append(
            {
                "source": "federal_register",
                "title": r.get("title"),
                "publication_date": to_utc(r.get("publication_date")),
                "doc_type": r.get("type"),
                "document_number": r.get("document_number"),
                "url": r.get("html_url"),
                "agencies": ags,
                "retrieved_utc": _utcnow(),
            }
        )
    return pd.DataFrame(rows).drop_duplicates(subset=["document_number"]).reset_index(drop=True)


# -----------------------------
# Tasks: Additional RSS
# -----------------------------
@task
def fetch_occ_rss(url: str = OCC_RSS) -> pd.DataFrame:
    p = feedparser.parse(url)
    rows = [{
        "source":"occ_rss","title":e.get("title"),
        "published_utc": to_utc(e.get("published") or e.get("updated")),
        "url": e.get("link"), "summary": e.get("summary"),
        "retrieved_utc": _utcnow()} for e in p.entries]
    if not rows: raise ExpectedEmpty("No OCC items")
    return pd.DataFrame(rows).drop_duplicates(subset=["url","title"]).reset_index(drop=True)


@task
def fetch_fdic_rss(url: str = FDIC_RSS) -> pd.DataFrame:
    p = feedparser.parse(url)
    rows = [{
        "source":"fdic_rss","title":e.get("title"),
        "published_utc": to_utc(e.get("published") or e.get("updated")),
        "url": e.get("link"), "summary": e.get("summary"),
        "retrieved_utc": _utcnow()} for e in p.entries]
    if not rows: raise ExpectedEmpty("No FDIC items")
    return pd.DataFrame(rows).drop_duplicates(subset=["url","title"]).reset_index(drop=True)


@task
def fetch_sec_rss(url: str = SEC_RSS) -> pd.DataFrame:
    # Press releases; SEC may rate-limit scraping—this is just a lightweight signal feed
    p = feedparser.parse(url)
    rows = [{
        "source":"sec_rss","title":e.get("title"),
        "published_utc": to_utc(e.get("published") or e.get("updated")),
        "url": e.get("link"), "summary": e.get("summary"),
        "retrieved_utc": _utcnow()} for e in p.entries]
    if not rows: raise ExpectedEmpty("No SEC items")
    return pd.DataFrame(rows).drop_duplicates(subset=["url","title"]).reset_index(drop=True)


# -----------------------------
# Tasks: Macro calendars (optional)
# -----------------------------
@task
def fetch_finnhub_calendar(as_of_date: datetime) -> pd.DataFrame:
    key = os.environ.get("FINNHUB_API_KEY")
    if not key:
        raise ExpectedEmpty("FINNHUB_API_KEY not set; skipping")
    try:
        import finnhub  # type: ignore
    except Exception:
        raise ExpectedEmpty("finnhub-python not installed; pip install finnhub-python")

    api = finnhub.Client(api_key=key)
    d0 = (as_of_date.date()).isoformat()
    d1 = (as_of_date.date() + timedelta(days=1)).isoformat()
    cal = api.calendar_economic(_from=d0, to=d1) or {}
    rows = cal.get("economicCalendar", [])
    if not rows:
        raise ExpectedEmpty("No Finnhub econ releases")
    df = pd.DataFrame(rows)
    df["source"] = "finnhub_calendar"
    df["retrieved_utc"] = _utcnow()
    return df


@task
def fetch_te_calendar(as_of_date: datetime) -> pd.DataFrame:
    client = os.environ.get("TE_API_CLIENT")
    api_key = os.environ.get("TE_API_KEY")
    if not (client and api_key):
        raise ExpectedEmpty("TE_API_CLIENT/TE_API_KEY not set; skipping")
    try:
        import tradingeconomics as te  # type: ignore
    except Exception:
        raise ExpectedEmpty("tradingeconomics not installed; pip install tradingeconomics")

    te.login(client, api_key)
    d = as_of_date.date().isoformat()
    data = te.getCalendarData(initDate=d, endDate=d) or []
    if not data:
        raise ExpectedEmpty("No TE calendar rows")
    df = pd.DataFrame(data)
    df["source"] = "trading_economics"
    df["retrieved_utc"] = _utcnow()
    return df


# -----------------------------
# Loader
# -----------------------------
@task
def load_to_duckdb(db_path: str, table: str, df: pd.DataFrame) -> int:
    con = duckdb.connect(db_path)
    try:
        upsert_df(con, df, table)
    finally:
        con.close()
    return len(df)


# -----------------------------
# Flow (DAG)
# -----------------------------
@flow(name="daily-news-and-events")
def daily_flow(db_path: str, as_of_iso: Optional[str] = None) -> Dict[str, int]:
    logger = get_run_logger()

    # as-of date (default yesterday UTC)
    if as_of_iso:
        as_of = dateparser.parse(as_of_iso)
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=timezone.utc)
        as_of = as_of.astimezone(timezone.utc)
    else:
        as_of = (_utcnow() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    logger.info(f"Running as_of={as_of.isoformat()} → db={db_path}")
    counts: Dict[str, int] = {}

    # Core
    try:
        fed_df = fetch_fed_rss.submit(FED_RSS_FEEDS).result()
        counts["fed_rss"] = load_to_duckdb.submit(db_path, "fed_rss", fed_df).result()
    except ExpectedEmpty:
        counts["fed_rss"] = 0

    try:
        tr_df = fetch_treasury_upcoming_auctions.submit(as_of).result()
        counts["treasury_auctions"] = load_to_duckdb.submit(db_path, "treasury_auctions", tr_df).result()
    except ExpectedEmpty:
        counts["treasury_auctions"] = 0
    except Exception as e:
        logger.warning(f"Treasury auctions task soft-failed: {e}")
        counts["treasury_auctions"] = -1

    try:
        fr_df = fetch_federal_register_docs.submit(as_of).result()
        counts["federal_register"] = load_to_duckdb.submit(db_path, "federal_register", fr_df).result()
    except ExpectedEmpty:
        counts["federal_register"] = 0

    # Additional RSS (regulatory)
    for task_fn, tbl, key in [
        (fetch_occ_rss, "occ_rss", "occ_rss"),
        (fetch_fdic_rss, "fdic_rss", "fdic_rss"),
        (fetch_sec_rss,  "sec_rss",  "sec_rss"),
    ]:
        try:
            df = task_fn.submit().result()
            counts[key] = load_to_duckdb.submit(db_path, tbl, df).result()
        except ExpectedEmpty:
            counts[key] = 0
        except Exception as e:
            logger.warning(f"{key} task soft-failed: {e}")
            counts[key] = -1

    # Macro calendars (optional, run both if available)
    for task_fn, tbl, key in [
        (fetch_finnhub_calendar, "econ_calendar_finnhub", "econ_calendar_finnhub"),
        (fetch_te_calendar,      "econ_calendar_te",      "econ_calendar_te"),
    ]:
        try:
            df = task_fn.submit(as_of).result()
            counts[key] = load_to_duckdb.submit(db_path, tbl, df).result()
        except ExpectedEmpty:
            counts[key] = 0
        except Exception as e:
            logger.warning(f"{key} task soft-failed: {e}")
            counts[key] = -1

    logger.info(f"Done. Row counts: {counts}")
    return counts


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Daily monitoring DAG for news/events → DuckDB")
    p.add_argument("--db", type=str, default="./hqlamonitor.duckdb", help="Path to DuckDB database")
    p.add_argument("--date", type=str, default=None, help="As-of date (YYYY-MM-DD). Defaults to yesterday (UTC).")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    out = daily_flow(db_path=args.db, as_of_iso=args.date)
    print(json.dumps(out, indent=2, default=str))
