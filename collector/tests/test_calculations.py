import pytest
from calculations import (change_bps, change_pct, change_points, spread_bps, latest_two,
    combine_target_ranges, latest_fed_move, generate_signals, classify_regime, summarize)
from fred import parse_observations
from news import parse_seendate, score_article, has_supporting_news
from update import build_snapshot
from tests.fixtures import SAMPLE_SERIES, SAMPLE_HEADLINES


def test_change_bps():
    assert change_bps(4.31, 4.38) == -7.0
    assert change_bps(None, 4.0) is None

def test_change_pct():
    assert change_pct(100, 102) == -1.96
    assert change_pct(1, 0) is None

def test_points_and_spread():
    assert change_points(15.70, 17.71) == -2.01
    assert spread_bps(4.31, 4.55) == -24.0
    assert spread_bps(None, 4.55) is None

def test_latest_two_edge_cases():
    assert latest_two([]) == (None, None)
    assert latest_two([{"value": 1.0}]) == (1.0, None)

def test_parse_skips_missing_and_sorts():
    raw = [{"date": "2026-09-14", "value": "4.1"}, {"date": "2026-09-15", "value": "."},
           {"date": "2026-09-16", "value": "4.3"}]
    out = parse_observations("DGS10", raw)
    assert [o["observation_date"] for o in out] == ["2026-09-16", "2026-09-14"]

def test_fed_move_hike_and_effective_date():
    r = combine_target_ranges(SAMPLE_SERIES["DFEDTARL"], SAMPLE_SERIES["DFEDTARU"])
    assert latest_fed_move(r) == (25.0, "2026-09-17")

def test_fed_move_cut_after_long_hold():
    lo = [{"observation_date": f"2026-01-{d:02d}", "value": 3.50 if d >= 5 else 3.75} for d in range(1, 29)]
    hi = [{"observation_date": x["observation_date"], "value": x["value"] + 0.25} for x in lo]
    lo.reverse(); hi.reverse()
    assert latest_fed_move(combine_target_ranges(lo, hi)) == (-25.0, "2026-01-05")

def test_fed_move_no_history():
    r = combine_target_ranges(SAMPLE_SERIES["DFEDTARL"][:1], SAMPLE_SERIES["DFEDTARU"][:1])
    assert latest_fed_move(r) == (None, None)

def test_signals_none_safe():
    assert generate_signals({}) == []
    assert classify_regime({})["rates"] == "No data"

def test_signals_directions():
    sigs = generate_signals({"treasury_10y_change_bps": -7, "wti_change_pct": -2.8,
                             "vix_change_points": -2.0, "sp500_change_pct": 0.9})
    assert {s["key"]: s["direction"] for s in sigs} == {
        "rates10y": "down", "oil": "down", "vix": "down", "equities": "up"}
    text = summarize(sigs, {"equities": "Rising"}, 0.9)
    assert "easing" in text and "rose 0.90%" in text

def test_regime_flattening():
    assert classify_regime({"treasury_2y_change_bps": 4, "treasury_10y_change_bps": -7})["rates"] == "Curve flattening"

def test_seendate():
    assert parse_seendate("20260917T123000Z") == "2026-09-17T12:30:00+00:00"
    assert parse_seendate("bad") is None

def test_scoring_and_support():
    assert score_article({"title": "Federal Reserve raises rates", "domain": "reuters.com"}) == 10
    assert has_supporting_news("oil", SAMPLE_HEADLINES)[0]["url"] == "https://example.com/a"

def test_build_snapshot_uses_market_date_not_clock():
    s = build_snapshot(SAMPLE_SERIES, SAMPLE_HEADLINES)
    assert s["snapshot_date"] == "2026-09-16"
    assert s["fed_latest_move_bps"] == 25.0
    assert s["curve_2s10s_bps"] == -24.0
    assert s["treasury_10y_change_bps"] == -7.0
    assert s["signals"]

def test_build_snapshot_survives_missing_series():
    partial = {k: v for k, v in SAMPLE_SERIES.items() if k not in ("DCOILWTICO", "T10YIE")}
    s = build_snapshot(partial)
    assert s["wti"] is None and s["wti_change_pct"] is None

def test_build_snapshot_refuses_empty():
    with pytest.raises(RuntimeError):
        build_snapshot({})


def test_parse_csv_handles_both_headers_and_missing():
    from fred import parse_csv
    text = "observation_date,DGS10\n2026-09-14,4.10\n2026-09-15,\n2026-09-16,4.30\n"
    out = parse_csv("DGS10", text)
    assert [o["observation_date"] for o in out] == ["2026-09-16", "2026-09-14"]
    assert parse_csv("DGS10", "DATE,DGS10\n2026-09-16,.\n2026-09-17,4.2\n")[0]["value"] == 4.2

def test_parse_csv_rejects_html():
    from fred import parse_csv
    with pytest.raises(RuntimeError, match="unexpected CSV header"):
        parse_csv("DGS10", "<!DOCTYPE html><html>blocked</html>")

def test_get_series_falls_back_to_csv(monkeypatch):
    import fred

    class Resp:
        def __init__(self, text, ctype):
            self.text, self.status_code, self.headers = text, 200, {"Content-Type": ctype}
        def raise_for_status(self):
            pass
        def json(self):
            import json
            return json.loads(self.text)

    def fake_get(url, **kw):
        if url == fred.BASE_URL:
            return Resp("<html>Access denied</html>", "text/html")
        return Resp("observation_date,DGS10\n2026-09-15,4.38\n2026-09-16,4.31\n", "text/csv")

    monkeypatch.setenv("FRED_API_KEY", "x")
    monkeypatch.setattr(fred.requests, "get", fake_get)
    monkeypatch.setattr(fred.time, "sleep", lambda s: None)
    out = fred.get_series("DGS10", limit=1)
    assert out == [{"series_id": "DGS10", "observation_date": "2026-09-16", "value": 4.31}]

def test_maintenance_page_raises_fred_unavailable_without_retrying(monkeypatch):
    import fred
    calls = []

    class Resp:
        status_code, headers = 200, {"Content-Type": "text/html"}
        text = "<!doctype html><html><head><title>Site Maintenance | St. Louis Fed</title>"
        def raise_for_status(self):
            pass
        def json(self):
            raise ValueError("not json")

    def fake_get(url, **kw):
        calls.append(url)
        return Resp()

    monkeypatch.setenv("FRED_API_KEY", "x")
    monkeypatch.setattr(fred.requests, "get", fake_get)
    monkeypatch.setattr(fred.time, "sleep", lambda s: None)
    with pytest.raises(fred.FredUnavailable):
        fred.get_series("DGS10", limit=1)
    assert calls == [fred.BASE_URL, fred.CSV_URL]  # one API try, one CSV try

def test_update_skips_remaining_series_once_fred_is_down(monkeypatch):
    import fred, update
    calls = []
    def down(sid, **kw):
        calls.append(sid)
        raise fred.FredUnavailable("down")
    monkeypatch.setattr(fred, "get_series", down)
    series, failures, fred_down = update.update_market_data(store=False)
    assert fred_down and len(calls) == 1
    assert failures == list(update.SERIES) and all(v == [] for v in series.values())
