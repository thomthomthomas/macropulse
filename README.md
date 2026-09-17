# MacroPulse

A daily cross-asset dashboard: Fed policy, Treasury yields, breakevens, oil and VIX, linked to the equity move, with ranked macro headlines and a rule-based "Why markets moved" panel.

```
GitHub Actions (07:00 + 21:00 SGT, weekdays)
  -> collector/update.py -> FRED + GDELT -> Supabase
  -> POST /api/revalidate  -> Vercel (Next.js) refreshes instantly
```

## What's verified

- `collector`: 16 unit tests pass (bp/% maths, Fed move vs previous distinct range, missing data, weekend handling, signal engine, GDELT date parsing). `python update.py --dry-run` prints a full snapshot from fixtures.
- `frontend`: `npm run build` and `eslint` pass on Next.js 16. Without Supabase keys it runs in sample-data mode (see `docs/preview-*.png`).
- Not verifiable in the build sandbox: live calls to FRED, GDELT and Supabase. Do step 7 below to confirm those.

## Setup (about 30 minutes)

### 1. Get keys
- FRED API key: https://fred.stlouisfed.org/docs/api/api_key.html
- Supabase: create a free project at https://supabase.com. From Project Settings > API copy the **Project URL**, the **anon/publishable key**, and the **service_role/secret key**.
- A GitHub account and a Vercel account (sign in with GitHub).

### 2. Create the database
Supabase > SQL Editor > New query > paste `supabase/schema.sql` > Run. It creates the tables, seeds series metadata, and adds read-only access for the website.

### 3. Run the collector locally
```bash
cd collector
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # fill in FRED_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
python -m pytest -q
python update.py --dry-run  # no network
python update.py            # real run: rows appear in Supabase
```

### 4. Push to GitHub
```bash
git init && git add . && git commit -m "MacroPulse v1"
git branch -M main
git remote add origin https://github.com/<you>/macropulse.git
git push -u origin main
```
`.env` files are git-ignored. Check with `git status` before pushing.

### 5. Deploy the site on Vercel
Vercel > Add New Project > import the repo > set **Root Directory** to `frontend`. Add environment variables:

| Name | Value |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | anon/publishable key (never the service key) |
| `REVALIDATE_SECRET` | any long random string |

Deploy, then note your URL, e.g. `https://macropulse-xyz.vercel.app`.

Local dev: `cd frontend && cp .env.example .env.local && npm install && npm run dev`.

### 6. Turn on daily updates
GitHub repo > Settings > Secrets and variables > Actions > New repository secret:

| Secret | Value |
|---|---|
| `FRED_API_KEY` | FRED key |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | service_role/secret key |
| `SITE_URL` | your Vercel URL, no trailing slash |
| `REVALIDATE_SECRET` | same string as on Vercel |

Also: Settings > Actions > General > Workflow permissions > **Read and write** (needed for the monthly keepalive commit).

### 7. Confirm it works
1. Actions tab > Daily Macro Update > **Run workflow**. The log should end with `COMPLETE`.
2. Supabase > Table editor: `daily_snapshot` has a row, `news` has headlines, `update_runs` shows `ok`.
3. Open the site: the sample-data banner is gone and the masthead shows today's update time.

## How the daily update behaves

- Runs 23:00 UTC Sun–Fri (07:00 SGT, after the US close) and 13:00 UTC Mon–Fri (21:00 SGT) to catch series FRED publishes late. Upserts make re-runs harmless.
- The snapshot is keyed to the latest US market date, not the runner's clock, so weekends and holidays never produce blank or duplicate days.
- Daily changes compare the two latest valid observations. WTI on FRED often lags by a few days; each card shows its own observation date.
- One failed series or news topic does not stop the run. The job fails (and GitHub emails you) only if 2Y, 10Y, Fed target or S&P data is missing.
- GitHub pauses schedules after 60 days of repo inactivity; the workflow pushes an empty commit on the 1st of each month to prevent that.
- Scheduled runs can start 5 to 30 minutes late at busy times. That is normal for GitHub Actions.
- Headlines older than 30 days are deleted automatically; the site shows the last 48 hours.

## Yearly maintenance
- Add the next year's FOMC dates to `frontend/lib/fomc.ts` from https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm.

## Changes from the original build guide
- Fed series fetched with full history, so the "latest move" finds the previous distinct range (30 rows usually doesn't).
- Snapshot date from market data instead of `date.today()` (the UTC runner is on the previous calendar day at 07:00 SGT).
- All calculations are None-safe; the guide's VIX and 2s10s lines crashed on missing data.
- GDELT `seendate` converted to ISO timestamps (Postgres rejects the raw format); requests spaced 6 s apart per GDELT's rate limit; non-JSON error responses handled.
- Chart query fixed to return the most recent year, not the oldest rows.
- Row Level Security policies added so the anon key can only read.
- Cron in UTC; `timezone:` isn't a reliable key in GitHub schedules.
- Headline score stored and used; news support attached to each signal ("Supported by news" vs "Data signal only").
- Site re-renders every 30 minutes and instantly after each update via `/api/revalidate`.
- Run log table (`update_runs`) for monitoring.

## Next features (from the guide, in order)
Optional FRED series (3M/5Y/30Y, real yields, CPI/PCE, HY spreads), a full yield-curve view, an economic calendar, a correlation explorer, then an LLM summary fed only with the stored snapshot and headlines.
