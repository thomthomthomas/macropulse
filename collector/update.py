"""Daily MacroPulse updater.

    python update.py            full run: FRED + GDELT -> Supabase
    python update.py --dry-run  use fixtures, print snapshot, touch nothing
"""
import json
import sys
from datetime import datetime, timezone

from config import SERIES, MARKET_DATE_SERIES
from calculations import (
    latest_two, latest_date, change_bps, change_pct, change_points, spread_bps,
    combine_target_ranges, latest_fed_move, generate_signals, classify_regime,
    summarize,
)
from log import log


def update_market_data(store=True):
    from fred import get_series
    all_series, failures = {}, []
    for sid, (_label, start, limit) in SERIES.items():
        try:
            obs = get_series(sid, limit=limit, observation_start=start)
            if store:
                from database import upsert_observations
                # store only the recent window for deep-history series
                upsert_observations(obs if limit else obs[:400])
            all_series[sid] = obs
            log(f"{sid} OK ({len(obs)} obs, latest {latest_date(obs)})")
        except Exception as e:
            failures.append(sid)
            all_series[sid] = []
            log(f"{sid} FAILED {e}")
    return all_series, failures


def build_snapshot(series, headlines=()):
    ranges = combine_target_ranges(series.get("DFEDTARL", []), series.get("DFEDTARU", []))
    current = ranges[0] if ranges else {}
    fed_move, fed_eff = latest_fed_move(ranges)

    effr, _ = latest_two(series.get("DFF", []))
    y2, y2p = latest_two(series.get("DGS2", []))
    y10, y10p = latest_two(series.get("DGS10", []))
    be, bep = latest_two(series.get("T10YIE", []))
    oil, oilp = latest_two(series.get("DCOILWTICO", []))
    vix, vixp = latest_two(series.get("VIXCLS", []))
    spx, spxp = latest_two(series.get("SP500", []))

    dates = [latest_date(series.get(s, [])) for s in MARKET_DATE_SERIES]
    market_date = max((d for d in dates if d), default=None)
    if market_date is None:
        raise RuntimeError("No market data available; refusing to write an empty snapshot")

    snap = {
        "snapshot_date": market_date,
        "fed_lower": current.get("lower"),
        "fed_upper": current.get("upper"),
        "fed_midpoint": current.get("midpoint"),
        "fed_latest_move_bps": fed_move,
        "fed_move_effective_date": fed_eff,
        "effr": effr,
        "treasury_2y": y2, "treasury_2y_change_bps": change_bps(y2, y2p),
        "treasury_10y": y10, "treasury_10y_change_bps": change_bps(y10, y10p),
        "curve_2s10s_bps": spread_bps(y10, y2),
        "breakeven_10y": be, "breakeven_change_bps": change_bps(be, bep),
        "wti": oil, "wti_change_pct": change_pct(oil, oilp),
        "vix": vix, "vix_change_points": change_points(vix, vixp),
        "sp500": spx, "sp500_change_pct": change_pct(spx, spxp),
        "observation_dates": {sid: latest_date(obs) for sid, obs in series.items()},
    }

    signals = generate_signals(snap)
    if headlines:
        from news import has_supporting_news
        for s in signals:
            support = has_supporting_news(s["key"], headlines)
            s["news_support"] = [{"title": h["title"], "url": h["url"], "domain": h["domain"]}
                                 for h in support]
    regime = classify_regime(snap)
    snap["signals"] = signals
    snap["regime"] = regime
    snap["summary"] = summarize(signals, regime, spx)
    snap["generated_at"] = datetime.now(timezone.utc).isoformat()
    return snap


def run():
    started = datetime.now(timezone.utc)
    log("Starting update")
    from database import upsert_snapshot, upsert_news, prune_news, log_run
    from news import fetch_news

    series, failures = update_market_data(store=True)

    headlines = fetch_news(log=log)
    try:
        upsert_news(headlines)
        prune_news(30)
        log(f"{len(headlines)} headlines stored")
    except Exception as e:
        log(f"news store FAILED {e}")

    snap = build_snapshot(series, headlines)
    upsert_snapshot(snap)
    log(f"Snapshot stored for {snap['snapshot_date']}: {snap['summary']}")

    status = "ok" if not failures else ("partial" if len(failures) < len(SERIES) else "failed")
    try:
        log_run({"started_at": started.isoformat(), "status": status,
                 "failed_series": failures, "headline_count": len(headlines),
                 "snapshot_date": snap["snapshot_date"]})
    except Exception as e:
        log(f"run log FAILED {e}")
    log("COMPLETE" if status == "ok" else f"COMPLETE with status={status}")
    # Fail the GitHub Action (so you get an email) if critical series are missing
    if any(s in failures for s in ("DGS2", "DGS10", "DFEDTARU", "SP500")):
        sys.exit(1)


def dry_run():
    from tests.fixtures import SAMPLE_SERIES, SAMPLE_HEADLINES
    snap = build_snapshot(SAMPLE_SERIES, SAMPLE_HEADLINES)
    print(json.dumps(snap, indent=2))


if __name__ == "__main__":
    dry_run() if "--dry-run" in sys.argv else run()
