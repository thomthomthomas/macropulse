# MacroPulse
MacroPulse is a small automated system that tracks the state of macro markets and tries to explain, in plain language, why they moved on a given day.
## Structure

```
macropulse/
├── collector/          Python. Pulls data, does the math, writes to Supabase.
│   ├── config.py         Which FRED series to track, and the thresholds that decide
│   │                      whether a move counts as "notable."
│   ├── fred.py            Talks to the FRED API, cleans up the response.
│   ├── news.py            Talks to the GDELT API, scores and dedupes headlines.
│   ├── calculations.py    All the pure math: bp/% changes, the Fed-move logic,
│   │                      the signal rules, the regime classifier. No network calls —
│   │                      this is the file the tests actually exercise.
│   ├── database.py        Everything that writes to Supabase.
│   ├── update.py          The entry point. Runs the whole pipeline end to end.
│   └── tests/             16 tests against calculations.py, using fixture data.
│
├── supabase/
│   └── schema.sql       Five tables (below), seed data, and the read-only policy
│                          for the public/anon key.
│
├── frontend/            Next.js. Reads from Supabase, renders the dashboard.
│   ├── lib/
│   │   ├── data.ts         Fetches the latest snapshot, news and rate history.
│   │   │                    No calculations here — that's all done upstream.
│   │   ├── demo.ts         Sample data shown when no Supabase keys are set.
│   │   └── fomc.ts         Hardcoded FOMC meeting dates (the one manual bit).
│   ├── components/       MetricStrip, WhyMarketsMoved, RatesChart, NewsList.
│   └── app/
│       ├── page.tsx        The dashboard itself.
│       ├── sources/         A page listing where every number comes from.
│       └── api/revalidate/  Endpoint the daily job hits to force an instant refresh.
│
└── .github/workflows/
    └── daily-update.yml   Runs collector/update.py on a schedule.
```

## How data moves through it

**1. Collect.** Twice on weekdays, GitHub Actions runs `collector/update.py`. It pulls nine FRED series (Fed funds target, 2Y/10Y Treasuries, breakeven inflation, WTI, VIX, S&P 500) and headlines from five GDELT topic queries (Fed, rates, inflation, oil, equities).

**2. Compute.** Still inside `update.py`, the raw numbers get turned into something readable: day-over-day changes in bp/%, the 2s10s spread, the Fed's latest rate move measured against its *previous distinct* target range (not just yesterday's row), a handful of rule-based signals ("VIX moved more than 1pt" etc.), a five-line regime classification (rates/inflation/oil/vol/equities: rising, falling, flat), and a one-sentence plain-English summary built from whichever signals actually fired.

**3. Check against news.** Each signal gets matched against the day's headlines by keyword, so the dashboard can say whether a move is "supported by news" or just a data point on its own.

**4. Store.** Everything lands in Supabase: raw observations, the day's snapshot (one row, with signals/regime/summary as JSON columns), and the scored headlines. A `update_runs` table logs whether each run succeeded.

**5. Trigger a refresh.** If the run succeeds, it calls the Next.js site's `/api/revalidate` endpoint so the page updates immediately rather than waiting for its normal 30-minute cache window.

**6. Serve.** The Next.js site reads the latest snapshot, the last year of 2Y/10Y history, and the last 48 hours of headlines from Supabase, and renders them. If Supabase isn't configured yet, it falls back to sample data instead of showing a blank page.

## What's in the database

| Table | What it holds |
|---|---|
| `market_series` | Static metadata |
| `observations` | Every daily value ever pulled, keyed by series + date |
| `daily_snapshot` | One row per trading day: all the changes, signals, regime, summary |
| `news` | Scored headlines, deduped by URL and near-duplicate title |
| `update_runs` | A log of each collector run  |


## Timing and edge cases

The daily job runs twice on weekdays: 07:00 SGT (right after the US close) and again at 21:00 SGT, since FRED sometimes publishes a series a few hours late. Both runs are safe to repeat — everything upserts.

The snapshot date comes from the data itself, not the server's clock, so dating off the clock would mislabel the day. Daily changes always compare the two most recent *valid* observations, so weekends and holidays don't create gaps or fake zeroes. WTI in particular tends to lag a day or two on FRED, so each metric card shows its own observation date rather than assuming everything is from the same day.

If one series or one news topic fails to fetch, the run keeps going — it only fails outright (and emails you) if something critical like the 2Y, 10Y, Fed target, or S&P is missing. Old headlines clear out after 30 days; the site only shows the last 48 hours anyway. GitHub pauses scheduled workflows after 60 days without repo activity, so there's a step that pushes an empty commit once a month to keep the schedule alive.


Optional FRED series (3M/5Y/30Y, real yields, CPI/PCE, HY spreads), a full yield-curve view, an economic calendar, a correlation explorer, then an LLM summary fed only with the stored snapshot and headlines.
