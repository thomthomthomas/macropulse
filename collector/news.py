"""GDELT DOC 2.0 headline collector. Stores metadata only; never article bodies."""
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

QUERIES = {
    "fed":       '("Federal Reserve" OR FOMC OR Powell OR "rate cut" OR "rate hike") sourcelang:english',
    "rates":     '("Treasury yields" OR "bond yields" OR "10-year yield") sourcelang:english',
    "inflation": '(inflation OR CPI OR PCE) (Fed OR prices) sourcelang:english',
    "oil":       '("crude oil" OR "oil prices" OR WTI OR Brent OR OPEC) sourcelang:english',
    "equities":  '("S&P 500" OR Nasdaq OR "Wall Street" OR "stock market") sourcelang:english',
}

SOURCE_WEIGHT = {
    "reuters.com": 5, "bloomberg.com": 5, "wsj.com": 4, "ft.com": 4,
    "cnbc.com": 3, "apnews.com": 3, "marketwatch.com": 2, "barrons.com": 2,
    "finance.yahoo.com": 2, "federalreserve.gov": 5,
}

KEYWORDS = {
    "federal reserve": 5, "fomc": 5, "fed ": 3, "treasury": 4, "yield": 3,
    "inflation": 4, "cpi": 3, "oil": 3, "brent": 3, "wti": 3, "opec": 2,
    "rate hike": 5, "rate cut": 5, "s&p 500": 3, "stocks": 1, "powell": 3,
}


def get_domain(url):
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return None


def parse_seendate(value):
    """GDELT returns 20260917T123000Z; convert to ISO 8601 for Postgres."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return None


def score_article(article):
    title = (article.get("title") or "").lower() + " "
    score = SOURCE_WEIGHT.get(article.get("domain") or "", 1)
    for kw, pts in KEYWORDS.items():
        if kw in title:
            score += pts
    return score


def fetch_topic(topic, query, retries=2):
    params = {"query": query, "mode": "artlist", "maxrecords": 50,
              "timespan": "1d", "sort": "datedesc", "format": "json"}
    for attempt in range(retries + 1):
        r = requests.get(GDELT_URL, params=params, timeout=30,
                         headers={"User-Agent": "MacroPulse/1.0"})
        # GDELT returns plain-text errors (e.g. rate limit) with 200 status
        try:
            data = r.json()
            break
        except ValueError:
            if attempt == retries:
                raise RuntimeError(f"GDELT non-JSON response: {r.text[:120]}")
            time.sleep(8)

    rows = []
    for a in data.get("articles", []):
        url, title = a.get("url"), (a.get("title") or "").strip()
        if not url or not title:
            continue
        row = {
            "title": title[:400],
            "url": url,
            "domain": get_domain(url),
            "published_at": parse_seendate(a.get("seendate")),
            "image_url": a.get("socialimage") or None,
            "source_country": a.get("sourcecountry"),
            "language": a.get("language"),
            "topic": topic,
        }
        row["score"] = score_article(row)
        rows.append(row)
    return rows


def fetch_news(log=print):
    articles = []
    for i, (topic, query) in enumerate(QUERIES.items()):
        if i:
            time.sleep(6)  # GDELT asks for <= 1 request per 5 seconds
        try:
            rows = fetch_topic(topic, query)
            log(f"news:{topic} {len(rows)} articles")
            articles.extend(rows)
        except Exception as e:
            log(f"news:{topic} FAILED {e}")

    # Dedupe by URL and by near-identical title (syndicated copies)
    by_url, seen_titles = {}, set()
    for a in sorted(articles, key=lambda x: x["score"], reverse=True):
        key = "".join(ch for ch in a["title"].lower() if ch.isalnum())[:80]
        if a["url"] in by_url or key in seen_titles:
            continue
        seen_titles.add(key)
        by_url[a["url"]] = a
    return list(by_url.values())


def has_supporting_news(signal_key, headlines):
    """Does any recent headline talk about this signal's market?"""
    terms = {
        "rates2y": ("fed", "fomc", "rate", "powell", "treasury"),
        "rates10y": ("treasury", "yield", "bond"),
        "inflation": ("inflation", "cpi", "pce", "prices"),
        "oil": ("oil", "crude", "brent", "wti", "opec"),
        "vix": ("volatility", "vix", "selloff", "rally", "risk"),
        "equities": ("stocks", "s&p", "nasdaq", "wall street", "dow"),
    }.get(signal_key, ())
    matches = [h for h in headlines
               if any(t in (h.get("title") or "").lower() for t in terms)]
    matches.sort(key=lambda h: h.get("score", 0), reverse=True)
    return matches[:2]
