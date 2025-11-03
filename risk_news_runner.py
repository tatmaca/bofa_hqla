#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
risk_news_runner.py

Daily risk-news pipeline (ready to drop into your VS Code project).
- Normalizes & dedupes.
- Scores relevance to Liquidity / Credit / IRR via keyword rules.
- (Optional) Classifies with an LLM if OPENAI_API_KEY is set (can be turned off).
- Emits CSV + a Markdown daily digest grouped by topic.
"""

from __future__ import annotations
from pathlib import Path
import os, sys, re, json
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional

import feedparser
import pandas as pd
from dateutil import parser as dateparser

# --------------------------- Config ---------------------------

DEFAULT_SOURCES = [
    # Markets / media (open headlines)
    {"name": "investing_news", "url": "https://www.investing.com/rss/news.rss", "fetch": "title"},
    {"name": "marketwatch_headlines", "url": "https://www.marketwatch.com/rss/topstories.rss", "fetch": "title"},
    # Official / regulators
    {"name": "sec_press", "url": "https://www.sec.gov/news/pressreleases.rss", "fetch": "title"},
    {"name": "fed_board", "url": "https://www.federalreserve.gov/feeds/press_all.xml", "fetch": "title"},
    {"name": "fdic_press", "url": "https://www.fdic.gov/news/press-releases/index.xml", "fetch": "title"},
    {"name": "bis_qr", "url": "https://www.bis.org/rss/quarterlyreview.xml", "fetch": "title"},
]


# Topic taxonomy (simple keyword matching). Case-insensitive; use plain strings or regex prefixed with r/...
TAXONOMY = {
    "Liquidity": {
        "include": [
            "repo", "gc", "ois", "standing repo", "bid-ask", "discount window",
            "btfp", "money market", "commercial paper", "tga", "lcr", "nsfr",
            "liquidity coverage", "net stable funding", "market depth", "move index", "haircut"
        ],
        "exclude": ["movie", "moving"]
    },
    "Credit": {
        "include": [
            "credit spread", "oas", "cdx", "default", "downgrade", "upgrade",
            "fallen angel", "distress", "covenant", "high yield", "investment grade",
            "provision", "npl", "restructuring", "bankrupt", "chapter 11"
        ],
        "exclude": []
    },
    "IRR": {
        "include": [
            "yield curve", "2s10s", "2s/10s", "term premium", "auction tail",
            "fomc", "dot plot", "sofr", "dv01", "duration", "convexity", "qt", "qe"
        ],
        "exclude": []
    },
}

DOMAIN_BOOST = {
    "federalreserve.gov": 0.6,
    "sec.gov": 0.6,
    "fdic.gov": 0.5,
    "bis.org": 0.4,
    "reuters.com": 0.3,
}

# ------------------------- Utilities -------------------------

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def parse_rss_datetime(s: str | None) -> Optional[datetime]:
    if not s:
        return None
    try:
        dt = dateparser.parse(s)
        if not dt:
            return None
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def parse_rss_datetime_any(entry) -> Optional[datetime]:
    """Robust: published / updated / published_parsed / updated_parsed"""
    for key in ("published", "updated"):
        v = getattr(entry, key, None)
        if v:
            dt = parse_rss_datetime(v)
            if dt:
                return dt
    for key in ("published_parsed", "updated_parsed"):
        v = getattr(entry, key, None)
        if v:
            try:
                # feedparser gives time.struct_time
                ts = datetime(*v[:6], tzinfo=timezone.utc)
                return ts
            except Exception:
                pass
    return None

def clean_text(x: str | None) -> str:
    if not x:
        return ""
    x = re.sub(r"<[^>]+>", " ", x)  # strip HTML tags in summaries
    x = re.sub(r"\s+", " ", x).strip()
    return x

def sha1(s: str) -> str:
    import hashlib
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()

# -------------------------- Ingest ---------------------------

def fetch_rss(url: str, limit: int = 200) -> List[Dict[str, Any]]:
    feed = feedparser.parse(url)
    items = []
    src_title = clean_text(getattr(feed.feed, "title", "")) or url
    for e in feed.entries[:limit]:
        title = clean_text(getattr(e, "title", "")) or ""
        link = getattr(e, "link", "") or ""
        summ = clean_text(getattr(e, "summary", "")) or ""
        pub_dt = parse_rss_datetime_any(e)
        # If no date in feed item, fall back to "now" so it's not dropped by since filter
        pub_iso = (pub_dt or now_utc()).isoformat()

        items.append({
            "title": title,
            "summary": summ,
            "link": link,
            "published_at": pub_iso,
            "source_name": src_title,
            "source_url": url,
        })
    return items

# ---------------------- Scoring / Classify -------------------

def keyword_score(text: str, inc: List[str], exc: List[str]) -> float:
    txt = text.lower()
    score = 0.0
    for pat in inc:
        if pat.startswith("r/"):
            if re.search(pat[2:], txt):
                score += 1.0
        else:
            if pat.lower() in txt:
                score += 1.0
    for pat in exc:
        if pat.lower() in txt:
            score -= 1.0
    return score

def apply_rules(row: Dict[str, Any]) -> Dict[str, Any]:
    title = row["title"]
    summary = row["summary"]
    url = row["link"]
    domain = urlparse(url).netloc.lower()

    best_topic, best_score = None, 0.0
    details = {}

    text = f"{title}. {summary}" if summary else title
    for topic, cfg in TAXONOMY.items():
        s = keyword_score(text, cfg["include"], cfg["exclude"])
        # domain boost
        for d, w in DOMAIN_BOOST.items():
            if d in domain:
                s += w
        details[topic] = s
        if s > best_score:
            best_score, best_topic = s, topic

    row["topic_rule"] = best_topic if best_score > 0.8 else "None"
    row["score_rule"] = round(best_score, 3)
    row["score_breakdown"] = json.dumps(details)
    return row

# ---------------------- Optional: LLM ------------------------

def classify_with_llm(rows: List[Dict[str, Any]], model: str = "gpt-4o-mini") -> List[Dict[str, Any]]:
    """
    Optional LLM classification (topic + relevance). Requires OPENAI_API_KEY in env.
    If missing or any error, we skip gracefully.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return rows  # no-op

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except Exception:
        return rows

    system = (
        "You are a risk-news triage assistant. "
        "Classify each item as one of: Liquidity, Credit, IRR, or None. "
        "Output JSON: {topic, relevance: strong|medium|weak|none}. "
        "Use only the provided text; do not infer beyond it."
    )

    out = []
    for r in rows:
        text = (r["title"] or "") + " " + (r["summary"] or "")
        text = text[:1200]
        prompt = f"Text: {text}\nReturn JSON: "

        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            content = resp.choices[0].message.content.strip()
            m = re.search(r"\{.*\}", content, re.S)
            if m:
                js = json.loads(m.group(0))
                r["topic_llm"] = js.get("topic", "None")
                r["relevance_llm"] = js.get("relevance", "none")
            else:
                r["topic_llm"] = None
                r["relevance_llm"] = None
        except Exception:
            r["topic_llm"] = None
            r["relevance_llm"] = None
        out.append(r)
    return out

# ---------------------- Dedupe / Normalize -------------------

def normalize_and_dedupe(rows: List[Dict[str, Any]], since_days: int) -> List[Dict[str, Any]]:
    cutoff = now_utc() - timedelta(days=since_days)
    out, seen = [], set()
    for r in rows:
        pub = r.get("published_at")
        pub_dt = parse_rss_datetime(pub) if isinstance(pub, str) else pub
        if pub_dt is None:
            pub_dt = now_utc()  # fallback so it won't be dropped
        if pub_dt < cutoff:
            continue
        key = sha1((r.get("title","") + "|" + (r.get("link","") or "")).strip())
        if key in seen:
            continue
        seen.add(key)
        r["id"] = key
        r["published_at"] = pub_dt.isoformat()
        out.append(r)
    return out

# ------------------------ Rendering --------------------------

def render_markdown(rows: List[Dict[str, Any]], out_path_md: str, top_k_per_topic: int = 8) -> None:
    lines = []
    hdr = f"# Daily Risk News Digest — {datetime.now().date()}\n\n"
    lines.append(hdr)
    if not rows:
        lines.append("_No items found._\n")
    else:
        df = pd.DataFrame(rows)
        topic_col = "topic_llm" if "topic_llm" in df.columns and df["topic_llm"].notna().any() else "topic_rule"
        for topic in ["Liquidity", "Credit", "IRR", "None"]:
            sub = df[(df[topic_col] == topic)].copy()
            if "relevance_llm" in sub.columns:
                llm_boost = sub["relevance_llm"].map({"strong": 1.0, "medium": 0.5, "weak": 0.2}).fillna(0.0)
            else:
                llm_boost = 0.0
            sub["rank_score"] = sub["score_rule"].astype(float) + llm_boost
            sub = sub.sort_values("rank_score", ascending=False).head(top_k_per_topic)

            lines.append(f"## {topic}\n\n")
            if sub.empty:
                lines.append("_No items._\n\n")
                continue
            for _, row in sub.iterrows():
                published = row.get("published_at") or ""
                srcname = row.get("source_name") or urlparse(row.get("link","")).netloc
                title = row.get("title","").strip()
                url = row.get("link","")
                summary = row.get("summary","").strip()
                summary_short = (summary[:280] + "…") if len(summary) > 280 else summary
                lines.append(f"- **[{title}]({url})**  \n  _{srcname} • {published}_  \n  {summary_short}\n")
            lines.append("\n")

    Path(out_path_md).write_text("\n".join(lines), encoding="utf-8")

# ------------------------- Runner ----------------------------

def run(sources: List[Dict[str, Any]], since_days: int, limit: int, out_dir: str, use_llm: bool):
    all_rows = []
    for src in sources:
        try:
            items = fetch_rss(src["url"], limit=limit)
            for it in items:
                it["source_key"] = src["name"]
                it["text_for_scoring"] = clean_text(f"{it['title']} {it['summary']}")
                all_rows.append(it)
            print(f"[OK] {src['name']}: fetched {len(items)} items")
        except Exception as e:
            print(f"[WARN] {src['name']} failed: {e}")

    print(f"[SRC] total fetched: {len(all_rows)}")
    rows = normalize_and_dedupe(all_rows, since_days=since_days)
    print(f"[FILTER] after time-window & dedupe: {len(rows)}")
    rows = [apply_rules(r) for r in rows]

    if use_llm:
        rows = classify_with_llm(rows)

    out_dir_path = Path(out_dir).resolve()
    date_tag = datetime.now().strftime("%Y-%m-%d")
    out_dir_path.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(rows)
    csv_path = out_dir_path / f"news_{date_tag}.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"[OK] Saved CSV -> {csv_path} ({len(df)} rows)")

    md_path = out_dir_path / f"daily_digest_{date_tag}.md"
    render_markdown(rows, str(md_path))
    print(f"[OK] Saved Digest -> {md_path}")

# -------------------------- CLI ------------------------------

def main():
    import argparse
    p = argparse.ArgumentParser(description="Daily risk-news pipeline (open sources)")
    p.add_argument("--since", type=int, default=1, help="Lookback window in days (default: 1)")
    p.add_argument("--limit", type=int, default=200, help="Max items per feed (default: 200)")
    p.add_argument("--out", type=str, default="./data/news", help="Output directory (default: ./data/news)")
    p.add_argument("--llm", type=str, choices=["on","off"], default="off", help="Enable LLM classification if OPENAI_API_KEY is set")
    args = p.parse_args()

    use_llm = args.llm == "on"
    run(DEFAULT_SOURCES, since_days=args.since, limit=args.limit, out_dir=args.out, use_llm=use_llm)

if __name__ == "__main__":
    main()
