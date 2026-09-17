import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


def get_series(series_id, limit=20, observation_start=None, retries=3):
    """Return valid observations sorted newest -> oldest."""
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
            r = requests.get(BASE_URL, params=params, timeout=30)
            r.raise_for_status()
            return parse_observations(series_id, r.json().get("observations", []))
        except Exception as e:  # network blip / 429 / 5xx
            last_error = e
            time.sleep(2 * (attempt + 1))
    raise last_error


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
