"""Illustrative sample data (not real market data)."""

def _s(sid, pairs):
    return [{"series_id": sid, "observation_date": d, "value": v} for d, v in pairs]

SAMPLE_SERIES = {
    "DFEDTARL": _s("DFEDTARL", [("2026-09-17", 3.75), ("2026-09-16", 3.50), ("2026-09-15", 3.50)]),
    "DFEDTARU": _s("DFEDTARU", [("2026-09-17", 4.00), ("2026-09-16", 3.75), ("2026-09-15", 3.75)]),
    "DFF":   _s("DFF", [("2026-09-16", 3.83), ("2026-09-15", 3.58)]),
    "DGS2":  _s("DGS2", [("2026-09-16", 4.55), ("2026-09-15", 4.51)]),
    "DGS10": _s("DGS10", [("2026-09-16", 4.31), ("2026-09-15", 4.38)]),
    "T10YIE": _s("T10YIE", [("2026-09-16", 2.30), ("2026-09-15", 2.34)]),
    "DCOILWTICO": _s("DCOILWTICO", [("2026-09-15", 100.62), ("2026-09-14", 103.52)]),
    "VIXCLS": _s("VIXCLS", [("2026-09-16", 15.70), ("2026-09-15", 17.71)]),
    "SP500": _s("SP500", [("2026-09-16", 6612.4), ("2026-09-15", 6553.4)]),
}

SAMPLE_HEADLINES = [
    {"title": "Oil slides as supply fears ease", "url": "https://example.com/a", "domain": "example.com", "score": 6},
    {"title": "Treasury yields fall after Fed decision", "url": "https://example.com/b", "domain": "example.com", "score": 9},
]
