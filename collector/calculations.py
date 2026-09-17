"""Pure functions: no network, fully unit-tested."""
from config import SIGNAL_THRESHOLDS as T


def latest_two(series):
    """Two latest VALID observations (handles weekends/holidays)."""
    if not series:
        return None, None
    if len(series) < 2:
        return series[0]["value"], None
    return series[0]["value"], series[1]["value"]


def latest_date(series):
    return series[0]["observation_date"] if series else None


def change_bps(current, previous):
    if current is None or previous is None:
        return None
    return round((current - previous) * 100, 2)


def change_pct(current, previous):
    if current is None or previous is None or previous == 0:
        return None
    return round((current - previous) / previous * 100, 2)


def change_points(current, previous):
    if current is None or previous is None:
        return None
    return round(current - previous, 2)


def spread_bps(long_yield, short_yield):
    if long_yield is None or short_yield is None:
        return None
    return round((long_yield - short_yield) * 100, 2)


def combine_target_ranges(lower_series, upper_series):
    lower = {x["observation_date"]: x["value"] for x in lower_series}
    upper = {x["observation_date"]: x["value"] for x in upper_series}
    dates = sorted(set(lower) & set(upper), reverse=True)
    return [
        {"date": d, "lower": lower[d], "upper": upper[d],
         "midpoint": (lower[d] + upper[d]) / 2}
        for d in dates
    ]


def latest_fed_move(ranges):
    """(move_bps, effective_date) vs the previous DISTINCT range."""
    if not ranges:
        return None, None
    current = ranges[0]
    effective = current["date"]
    for item in ranges[1:]:
        if item["lower"] != current["lower"] or item["upper"] != current["upper"]:
            return round((current["midpoint"] - item["midpoint"]) * 100, 2), effective
        effective = item["date"]  # walk back to first day of current range
    return None, None


def _sig(factor, direction, value, unit, text, key):
    return {"factor": factor, "direction": direction, "value": value,
            "unit": unit, "interpretation": text, "key": key}


def generate_signals(s):
    """Rule engine. Every rule is None-safe; describes, never asserts cause."""
    out = []
    y2, y10 = s.get("treasury_2y_change_bps"), s.get("treasury_10y_change_bps")
    be, oil = s.get("breakeven_change_bps"), s.get("wti_change_pct")
    vix, spx = s.get("vix_change_points"), s.get("sp500_change_pct")

    if y2 is not None and abs(y2) >= T["rates_bps"]:
        out.append(_sig("2Y Treasury", "up" if y2 > 0 else "down", y2, "bp",
            "Markets priced a higher near-term policy path." if y2 > 0
            else "Markets priced a lower near-term policy path.", "rates2y"))
    if y10 is not None and abs(y10) >= T["rates_bps"]:
        out.append(_sig("10Y Treasury", "up" if y10 > 0 else "down", y10, "bp",
            "Long-term discount-rate pressure increased." if y10 > 0
            else "Long-term discount-rate pressure eased.", "rates10y"))
    if be is not None and abs(be) >= T["breakeven_bps"]:
        out.append(_sig("10Y breakeven", "up" if be > 0 else "down", be, "bp",
            "Market-based inflation expectations rose." if be > 0
            else "Market-based inflation expectations softened.", "inflation"))
    if oil is not None and abs(oil) >= T["oil_pct"]:
        out.append(_sig("WTI crude", "up" if oil > 0 else "down", oil, "%",
            "Energy-related inflation pressure increased." if oil > 0
            else "Energy-related inflation pressure eased.", "oil"))
    if vix is not None and abs(vix) >= T["vix_points"]:
        out.append(_sig("VIX", "up" if vix > 0 else "down", vix, "pts",
            "Equity risk pricing rose; appetite for risk weakened." if vix > 0
            else "Equity risk pricing declined; risk appetite improved.", "vix"))
    if spx is not None and abs(spx) >= T["spx_pct"]:
        out.append(_sig("S&P 500", "up" if spx > 0 else "down", spx, "%",
            "Equities advanced." if spx > 0 else "Equities declined.", "equities"))
    return out


def classify_regime(s):
    def trend(v, thr):
        if v is None:
            return "No data"
        return "Rising" if v >= thr else "Falling" if v <= -thr else "Flat"

    y2, y10 = s.get("treasury_2y_change_bps"), s.get("treasury_10y_change_bps")
    if y2 is None or y10 is None:
        rates = "No data"
    elif y2 >= 3 and y10 >= 3:
        rates = "Rising"
    elif y2 <= -3 and y10 <= -3:
        rates = "Falling"
    elif y2 - y10 >= 3:
        rates = "Curve flattening"
    elif y10 - y2 >= 3:
        rates = "Curve steepening"
    else:
        rates = "Mixed"

    return {
        "rates": rates,
        "inflation": trend(s.get("breakeven_change_bps"), 2),
        "oil": trend(s.get("wti_change_pct"), 1),
        "volatility": trend(s.get("vix_change_points"), 0.5),
        "equities": trend(s.get("sp500_change_pct"), 0.3),
    }


def summarize(signals, regime, spx_pct=None):
    """One plain sentence built only from the day's data."""
    if not signals:
        return "No indicator cleared its threshold; a quiet session across rates, oil and volatility."
    easing = sum(1 for x in signals if x["key"] in ("rates10y", "inflation", "oil", "vix") and x["direction"] == "down")
    tightening = sum(1 for x in signals if x["key"] in ("rates10y", "inflation", "oil", "vix") and x["direction"] == "up")
    if easing > tightening:
        tone = "consistent with easing rate and inflation pressure and a friendlier backdrop for equities"
    elif tightening > easing:
        tone = "consistent with building rate or inflation pressure and a tougher backdrop for equities"
    else:
        tone = "mixed, with offsetting pressure across rates, oil and volatility"
    if spx_pct is None:
        tail = ""
    elif abs(spx_pct) < 0.05:
        tail = " The S&P 500 finished roughly flat."
    else:
        tail = f" The S&P 500 {'rose' if spx_pct > 0 else 'fell'} {abs(spx_pct):.2f}%."
    return f"Today's moves are {tone}.{tail}"
