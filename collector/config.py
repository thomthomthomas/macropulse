"""Series configuration.

Fed target series need deep history so the 'previous distinct range'
can be found. (Fetching only the last 30 daily rows, as in the original
guide, usually contains no prior rate change -> Fed move shows as None.)
"""

# series_id: (label, observation_start, row limit)
SERIES = {
    "DFEDTARL":   ("Fed Lower Bound",          "2008-12-16", None),
    "DFEDTARU":   ("Fed Upper Bound",          "2008-12-16", None),
    "DFF":        ("Effective Fed Funds Rate", None, 400),
    "DGS2":       ("2Y Treasury",              None, 400),
    "DGS10":      ("10Y Treasury",             None, 400),
    "T10YIE":     ("10Y Breakeven Inflation",  None, 400),
    "DCOILWTICO": ("WTI Crude Oil",            None, 400),
    "VIXCLS":     ("VIX",                      None, 400),
    "SP500":      ("S&P 500",                  None, 400),
}

# The snapshot is keyed by the latest US market date, not the runner's clock.
MARKET_DATE_SERIES = ("DGS10", "SP500", "VIXCLS")

# Thresholds for the "Why markets moved" rule engine
SIGNAL_THRESHOLDS = {
    "rates_bps": 5,
    "breakeven_bps": 3,
    "oil_pct": 2.0,
    "vix_points": 1.0,
    "spx_pct": 0.75,
}
