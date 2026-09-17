import type { Dashboard, RatePoint } from "./types";

// Illustrative sample shown only when Supabase is not configured.
function demoRates(): RatePoint[] {
  const out: RatePoint[] = [];
  const end = new Date("2026-09-16T00:00:00Z");
  let y2 = 4.1, y10 = 4.25;
  for (let i = 380; i >= 0; i--) {
    const d = new Date(end); d.setUTCDate(end.getUTCDate() - i);
    if (d.getUTCDay() === 0 || d.getUTCDay() === 6) continue;
    y2 += Math.sin(i / 17) * 0.02 + (i % 7 === 0 ? 0.01 : -0.004) + 0.0015;
    y10 += Math.cos(i / 23) * 0.018 + 0.0003;
    out.push({ date: d.toISOString().slice(0, 10), y2: +y2.toFixed(2), y10: +y10.toFixed(2) });
  }
  // shift so the last point matches the sample cards (2Y 4.55%, 10Y 4.31%)
  const last = out[out.length - 1];
  const d2 = 4.55 - (last.y2 ?? 0), d10 = 4.31 - (last.y10 ?? 0);
  return out.map((p) => ({ date: p.date, y2: +((p.y2 ?? 0) + d2).toFixed(2), y10: +((p.y10 ?? 0) + d10).toFixed(2) }));
}

export const demoDashboard: Dashboard = {
  mode: "demo",
  snapshot: {
    snapshot_date: "2026-09-16",
    fed_lower: 3.75, fed_upper: 4.0, fed_midpoint: 3.875,
    fed_latest_move_bps: 25, fed_move_effective_date: "2026-09-17",
    effr: 3.83,
    treasury_2y: 4.55, treasury_2y_change_bps: 4,
    treasury_10y: 4.31, treasury_10y_change_bps: -7,
    curve_2s10s_bps: -24,
    breakeven_10y: 2.3, breakeven_change_bps: -4,
    wti: 100.62, wti_change_pct: -2.8,
    vix: 15.7, vix_change_points: -2.01,
    sp500: 6612.4, sp500_change_pct: 0.9,
    observation_dates: { DGS10: "2026-09-16", DGS2: "2026-09-16", DCOILWTICO: "2026-09-15", VIXCLS: "2026-09-16", SP500: "2026-09-16", T10YIE: "2026-09-16", DFEDTARU: "2026-09-17" },
    signals: [
      { factor: "WTI crude", direction: "down", value: -2.8, unit: "%", key: "oil", interpretation: "Energy-related inflation pressure eased.", news_support: [{ title: "Sample: oil slides as supply fears ease", url: "#", domain: "example.com" }] },
      { factor: "10Y breakeven", direction: "down", value: -4, unit: "bp", key: "inflation", interpretation: "Market-based inflation expectations softened.", news_support: [] },
      { factor: "10Y Treasury", direction: "down", value: -7, unit: "bp", key: "rates10y", interpretation: "Long-term discount-rate pressure eased.", news_support: [{ title: "Sample: Treasury yields fall after Fed decision", url: "#", domain: "example.com" }] },
      { factor: "VIX", direction: "down", value: -2.01, unit: "pts", key: "vix", interpretation: "Equity risk pricing declined; risk appetite improved.", news_support: [] },
      { factor: "S&P 500", direction: "up", value: 0.9, unit: "%", key: "equities", interpretation: "Equities advanced.", news_support: [] },
    ],
    regime: { rates: "Curve flattening", inflation: "Falling", oil: "Falling", volatility: "Falling", equities: "Rising" },
    summary: "Today's moves are consistent with easing rate and inflation pressure and a friendlier backdrop for equities. The S&P 500 rose 0.90%.",
    generated_at: "2026-09-16T23:04:00Z",
  },
  news: [
    { title: "Sample headline: Fed raises target range by a quarter point", url: "#", domain: "example.com", published_at: "2026-09-16T18:10:00Z", topic: "fed", score: 13 },
    { title: "Sample headline: Treasury yields fall as long end rallies", url: "#", domain: "example.com", published_at: "2026-09-16T20:30:00Z", topic: "rates", score: 10 },
    { title: "Sample headline: Oil slides as supply fears ease", url: "#", domain: "example.com", published_at: "2026-09-16T15:00:00Z", topic: "oil", score: 7 },
    { title: "Sample headline: Wall Street closes higher as volatility fades", url: "#", domain: "example.com", published_at: "2026-09-16T20:05:00Z", topic: "equities", score: 6 },
  ],
  rates: demoRates(),
};
