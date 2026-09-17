-- MacroPulse schema. Paste into Supabase -> SQL Editor -> Run. Safe to re-run.

create table if not exists market_series (
    id text primary key,
    name text not null,
    category text not null,
    units text,
    source text default 'FRED'
);

create table if not exists observations (
    series_id text references market_series(id) on delete cascade,
    observation_date date not null,
    value numeric not null,
    fetched_at timestamptz default now(),
    primary key (series_id, observation_date)
);

create table if not exists news (
    id bigint generated always as identity primary key,
    title text not null,
    url text unique not null,
    domain text,
    published_at timestamptz,
    image_url text,
    source_country text,
    language text,
    topic text,
    score int default 0,
    fetched_at timestamptz default now()
);
create index if not exists news_published_idx on news (published_at desc);

create table if not exists daily_snapshot (
    snapshot_date date primary key,
    fed_lower numeric, fed_upper numeric, fed_midpoint numeric,
    fed_latest_move_bps numeric, fed_move_effective_date date,
    effr numeric,
    treasury_2y numeric, treasury_2y_change_bps numeric,
    treasury_10y numeric, treasury_10y_change_bps numeric,
    curve_2s10s_bps numeric,
    breakeven_10y numeric, breakeven_change_bps numeric,
    wti numeric, wti_change_pct numeric,
    vix numeric, vix_change_points numeric,
    sp500 numeric, sp500_change_pct numeric,
    observation_dates jsonb,
    signals jsonb,
    regime jsonb,
    summary text,
    generated_at timestamptz default now()
);

create table if not exists update_runs (
    id bigint generated always as identity primary key,
    started_at timestamptz,
    finished_at timestamptz default now(),
    status text,
    failed_series text[],
    headline_count int,
    snapshot_date date
);

insert into market_series (id, name, category, units) values
('DFEDTARL', 'Federal Funds Target Range - Lower Limit', 'Fed', '%'),
('DFEDTARU', 'Federal Funds Target Range - Upper Limit', 'Fed', '%'),
('DFF', 'Effective Federal Funds Rate', 'Fed', '%'),
('DGS2', '2-Year Treasury Constant Maturity', 'Rates', '%'),
('DGS10', '10-Year Treasury Constant Maturity', 'Rates', '%'),
('T10YIE', '10-Year Breakeven Inflation Rate', 'Inflation', '%'),
('DCOILWTICO', 'Crude Oil Prices: WTI', 'Commodities', 'USD/barrel'),
('VIXCLS', 'CBOE Volatility Index: VIX', 'Risk', 'index'),
('SP500', 'S&P 500', 'Equities', 'index')
on conflict (id) do nothing;

-- Housekeeping called by the collector
create or replace function prune_old_news(days int default 30)
returns void language sql security definer as $$
  delete from news where published_at < now() - make_interval(days => days);
$$;

-- Row Level Security: the website (anon key) may only READ.
-- The collector uses the service-role key, which bypasses RLS.
alter table market_series  enable row level security;
alter table observations   enable row level security;
alter table news           enable row level security;
alter table daily_snapshot enable row level security;
alter table update_runs    enable row level security;

drop policy if exists "public read" on market_series;
drop policy if exists "public read" on observations;
drop policy if exists "public read" on news;
drop policy if exists "public read" on daily_snapshot;
drop policy if exists "public read" on update_runs;
create policy "public read" on market_series  for select using (true);
create policy "public read" on observations   for select using (true);
create policy "public read" on news           for select using (true);
create policy "public read" on daily_snapshot for select using (true);
create policy "public read" on update_runs    for select using (true);
