# MacroPulse

A dashboard that tracks the Fed, Treasury yields, inflation expectations, oil and volatility, and connects them to what happened in equities that day. It pulls in ranked macro headlines and generates a "why markets moved" summary from the numbers rather than just showing raw data.

```
GitHub Actions (07:00 + 21:00 SGT, weekdays)
  -> collector/update.py -> FRED + GDELT -> Supabase
  -> POST /api/revalidate  -> Vercel (Next.js) refreshes instantly
```

## Setup

Takes about half an hour.

### 1. Get your keys
- FRED API key (free): https://fred.stlouisfed.org/docs/api/api_key.html
- A Supabase project (free): https://supabase.com. From Project Settings > API, grab the **Project URL**, the **anon/publishable key**, and the **service_role/secret key**.
- A GitHub account and a Vercel account (sign in with GitHub for both).

### 2. Set up the database
Supabase > SQL Editor > New query > paste in `supabase/schema.sql` > Run. This creates the tables, seeds the series metadata, and locks the site down to read-only access.

### 3. Run the collector once locally
```bash
cd collector
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # fill in FRED_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
python -m pytest -q
python update.py --dry-run  # no network, just checks the code works
python update.py            # real run — rows should appear in Supabase
```

### 4. Push to GitHub
```bash
git init && git add . && git commit -m "MacroPulse v1"
git branch -M main
git remote add origin https://github.com/<you>/macropulse.git
git push -u origin main
```
`.env` is git-ignored, but it's worth running `git status` before you push just to check.

### 5. Deploy on Vercel
Vercel > Add New Project > import the repo > set **Root Directory** to `frontend`. Add these environment variables:

| Name | Value |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | anon/publishable key (not the service key) |
| `REVALIDATE_SECRET` | any long random string you make up |

Deploy, then grab your URL — something like `https://macropulse-xyz.vercel.app`.

For local dev: `cd frontend && cp .env.example .env.local && npm install && npm run dev`.

### 6. Turn on the daily job
In the GitHub repo: Settings > Secrets and variables > Actions > New repository secret. Add:

| Secret | Value |
|---|---|
| `FRED_API_KEY` | your FRED key |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | service_role/secret key |
| `SITE_URL` | your Vercel URL, no trailing slash |
| `REVALIDATE_SECRET` | same string you used on Vercel |

Also go to Settings > Actions > General > Workflow permissions and switch it to **Read and write** — the monthly keepalive commit needs it.


## How the daily job works

It runs twice on weekdays: 07:00 SGT (right after the US close) and again at 21:00 SGT, since FRED sometimes publishes a series a few hours late. Both runs are safe to repeat — everything upserts, so nothing gets duplicated.

The snapshot date comes from the data itself, not the server's clock — otherwise a run at 07:00 SGT would think it's still "yesterday" in UTC and mislabel the day. Daily changes always compare the two most recent valid observations, so weekends and holidays don't create gaps or fake zeroes. WTI in particular tends to lag by a day or two on FRED, so each card shows its own observation date rather than assuming everything is from the same day.

If one series or one news topic fails to fetch, the run keeps going — it only fails outright (and emails you) if something critical like the 2Y, 10Y, Fed target, or S&P is missing. Old headlines get cleared out after 30 days; the site only ever shows the last 48 hours anyway.

GitHub pauses scheduled workflows after 60 days without any repo activity, so there's a small step that pushes an empty commit once a month just to keep the schedule alive. Runs can start a bit late (5–30 minutes) during busy periods — that's normal for GitHub Actions, not a bug.


Optional FRED series (3M/5Y/30Y, real yields, CPI/PCE, HY spreads), a full yield-curve view, an economic calendar, a correlation explorer, then an LLM summary fed only with the stored snapshot and headlines.
