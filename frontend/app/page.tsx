import Link from "next/link";
import { getDashboard } from "@/lib/data";
import { fixed, longDate, sgtTime, signed } from "@/lib/format";
import { nextFomc } from "@/lib/fomc";
import type { Snapshot, UpdateRun } from "@/lib/types";
import MetricStrip from "@/components/MetricStrip";
import WhyMarketsMoved from "@/components/WhyMarketsMoved";
import RatesChart from "@/components/RatesChart";
import NewsList from "@/components/NewsList";

// Re-render at most every 30 minutes; the daily job also triggers an instant refresh.
export const revalidate = 1800;

function fomcLabel() {
  const m = nextFomc();
  if (!m) return "Next FOMC: add dates in lib/fomc.ts";
  const f = (d: string) => new Date(d + "T00:00:00Z").toLocaleDateString("en-SG", { day: "numeric", month: "short", timeZone: "UTC" });
  return `Next FOMC ${f(m.start)}–${f(m.end)}`;
}

// Longest normal gap between updates is Fri 13:00 UTC -> Sun 23:00 UTC (58h).
const STALE_HOURS = 72;

function staleness(s: Snapshot | null, run: UpdateRun | null | undefined) {
  if (!s) return null;
  const ageH = (Date.now() - new Date(s.generated_at).getTime()) / 3_600_000;
  const lastFailed = run?.status === "failed" && run.finished_at != null
    && new Date(run.finished_at) > new Date(s.generated_at);
  if (!lastFailed && ageH < STALE_HOURS) return null;
  const when = lastFailed ? ` The latest update (${sgtTime(run!.finished_at)}) failed.` : "";
  return `Figures are from the US session of ${longDate(s.snapshot_date)}, last refreshed ${sgtTime(s.generated_at)}.${when}`;
}

export default async function Home() {
  const { snapshot: s, lastRun, news, rates, mode, error } = await getDashboard();
  const stale = mode === "live" ? staleness(s, lastRun) : null;

  return (
    <main className="wrap">
      <header className="masthead">
        <div className="brand">MacroPulse <span>Fed, rates, oil and why markets moved</span></div>
        <div className="masthead-meta">
          {s ? <>US session of <strong>{longDate(s.snapshot_date)}</strong><br />Updated {sgtTime(s.generated_at)}. {fomcLabel()}</> : fomcLabel()}
        </div>
      </header>

      {mode === "demo" && (
        <p className="banner"><strong>Sample data.</strong> Add your Supabase URL and anon key to see live figures. See README step 5.</p>
      )}
      {mode === "error" && (
        <p className="banner" role="alert"><strong>Couldn&apos;t reach the database.</strong> {error}. Check the Supabase environment variables and that schema.sql has been run.</p>
      )}
      {stale && (
        <p className="banner banner-warn" role="status"><strong>Data may be out of date.</strong> {stale}</p>
      )}
      {mode === "live" && !s && (
        <p className="banner"><strong>No snapshot yet.</strong> Run the &ldquo;Daily Macro Update&rdquo; workflow once from the GitHub Actions tab.</p>
      )}

      {s && <MetricStrip s={s} />}
      {s && <WhyMarketsMoved s={s} />}

      <div className="lower sec">
        <section aria-labelledby="rates">
          <div className="sec-head">
            <h2 className="sec-title" id="rates">Treasury yields</h2>
            <span className="sec-note">Daily constant-maturity yields</span>
          </div>
          <RatesChart data={rates} />
          {s && (
            <div className="curve-line">
              <span>2s10s <strong>{signed(s.curve_2s10s_bps, " bp")}</strong></span>
              <span>Fed midpoint <strong>{fixed(s.fed_midpoint, 3)}%</strong></span>
              <span>2Y minus midpoint <strong>{s.treasury_2y != null && s.fed_midpoint != null ? signed((s.treasury_2y - s.fed_midpoint) * 100, " bp") : "–"}</strong></span>
            </div>
          )}
        </section>

        <section aria-labelledby="news">
          <div className="sec-head">
            <h2 className="sec-title" id="news">Macro headlines</h2>
            <span className="sec-note">Last 48 hours, ranked</span>
          </div>
          <NewsList articles={news} />
        </section>
      </div>

      <footer className="footer">
        <span>Data via FRED, Federal Reserve Bank of St. Louis; underlying sources vary. Headlines via GDELT, linked to publishers. Not investment advice.</span>
        <Link href="/sources">Data sources</Link>
      </footer>
    </main>
  );
}
