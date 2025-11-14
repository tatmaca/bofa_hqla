from typing import Optional
import trafilatura, datetime as dt
from dateutil import parser as dtparse
from bs4 import BeautifulSoup

def extract(url: str, html: Optional[bytes] = None, *, metadata_only: bool = False):
    if metadata_only:
        # Best-effort: return title & published from lightweight parse if html provided
        if not html:
            return {"status": "paywalled", "title": None, "author": None, "published_at": None, "text": None}
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string.strip() if soup.title else None
        pub = None
        m = soup.find("meta", {"property":"article:published_time"}) or soup.find("meta", {"name":"pubdate"})
        if m and m.get("content"):
            try: pub = dtparse.parse(m["content"]).astimezone(dt.timezone.utc).isoformat()
            except: pass
        return {"status":"paywalled", "title":title, "author":None, "published_at":pub, "text":None}

    downloaded = html or trafilatura.fetch_url(url)
    if not downloaded:
        return {"status":"fetch_failed"}
    data = trafilatura.extract(downloaded, url=url, include_formatting=False,
                               include_links=False, favor_recall=True, with_metadata=True)
    if not data:
        return {"status":"extract_failed"}
    meta = trafilatura.bare_extraction(downloaded, url=url) or {}
    title = meta.get("title")
    author = meta.get("author")
    date = meta.get("date")
    if date:
        try: date = dtparse.parse(date).astimezone(dt.timezone.utc).isoformat()
        except: pass
    return {"title": title, "author": author, "published_at": date, "text": data, "status": "ok"}
