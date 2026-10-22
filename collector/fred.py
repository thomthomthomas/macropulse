import csv
import io
import os
import time
import requests
from dotenv import load_dotenv

from log import log

load_dotenv()

BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
# Public graph download: no API key, used when the JSON API misbehaves
# (e.g. it starts serving an HTML block/maintenance page with a 200 status).
CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

class FredUnavailable(RuntimeError):
    """FRED is serving its maintenance page: an outage, not a bug on our side."""


def _is_maintenance(text):
    return "site maintenance" in text[:2000].lower()


HEADERS = {
    "User-Agent": "MacroPulse/1.0 (+https://github.com/thomthomthomas/macropulse)",
    "Accept": "application/json, text/csv;q=0.9",
}


def get_series(series_id, limit=20, observation_start=None, retries=3):
    """Return valid observations sorted newest -> oldest."""
    try:
        return _get_series_api(series_id, limit, observation_start, retries)
    except Exception as api_error:
        try:
            obs = _get_series_csv(series_id, limit, observation_start)
        except FredUnavailable:
            if isinstance(api_error, FredUnavailable):
                raise FredUnavailable("FRED API and CSV download are both down for maintenance")
            raise RuntimeError(f"API: {api_error} | CSV fallback: FRED maintenance page")
        except Exception as csv_error:
            raise RuntimeError(f"API: {api_error} | CSV fallback: {csv_error}") from csv_error
        if not obs:
            raise RuntimeError(f"API: {api_error} | CSV fallback returned no rows")
        log(f"{series_id} JSON API failed ({api_error}); using CSV fallback")
        return obs


def _get_series_api(series_id, limit, observation_start, retries):
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise RuntimeError("FRED_API_KEY is not set")

    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
    }
    if limit:
        params["limit"] = limit
    if observation_start:
        params["observation_start"] = observation_start

    last_error = None
    for attempt in range(retries):
        try:
            r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
            r.raise_for_status()
            try:
                payload = r.json()
            except ValueError:
                if _is_maintenance(r.text):
                    raise FredUnavailable("FRED API is down for maintenance")
                # Surface what FRED actually sent instead of a bare JSONDecodeError
                snippet = " ".join(r.text[:120].split())
                raise RuntimeError(f"non-JSON response (HTTP {r.status_code}, "
                                   f"{r.headers.get('Content-Type', '?')}): {snippet!r}")
            return parse_observations(series_id, payload.get("observations", []))
        except FredUnavailable:
            raise  # retrying a maintenance page just wastes time
        except Exception as e:  # network blip / 429 / 5xx / HTML page
            last_error = e
            time.sleep(2 * (attempt + 1))
    raise last_error


def _get_series_csv(series_id, limit, observation_start):
    params = {"id": series_id}
    if observation_start:
        params["cosd"] = observation_start
    r = requests.get(CSV_URL, params=params, headers=HEADERS, timeout=60)
    r.raise_for_status()
    if _is_maintenance(r.text):
        raise FredUnavailable("FRED CSV download is down for maintenance")
    obs = parse_csv(series_id, r.text)
    return obs[:limit] if limit else obs


def parse_csv(series_id, text):
    """Parse fredgraph.csv (header: observation_date|DATE, <series_id>)."""
    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)
    if not header or len(header) < 2 or header[0].strip().lower() not in ("observation_date", "date"):
        raise RuntimeError(f"unexpected CSV header: {' '.join(text[:80].split())!r}")
    raw = [{"date": row[0].strip(), "value": row[1].strip()} for row in reader if len(row) >= 2]
    return parse_observations(series_id, raw)


def parse_observations(series_id, raw):
    out = []
    for item in raw:
        if item.get("value") in (".", "", None):  # FRED missing marker
            continue
        out.append({
            "series_id": series_id,
            "observation_date": item["date"],
            "value": float(item["value"]),
        })
    out.sort(key=lambda x: x["observation_date"], reverse=True)
    return out
