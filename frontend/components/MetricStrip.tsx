import type { Snapshot } from "@/lib/types";
import { arrow, dir, fixed, pct, shortDate, signed } from "@/lib/format";
import Tip from "./Tip";

type Item = {
  name: string; value: string; change: number | null; changeText: string;
  foot: string; tip: string;
};

export default function MetricStrip({ s }: { s: Snapshot }) {
  const od = s.observation_dates ?? {};
  const items: Item[] = [
    {
      name: "Fed target",
      value: s.fed_lower != null ? `${fixed(s.fed_lower)}–${fixed(s.fed_upper)}%` : "–",
      change: s.fed_latest_move_bps,
      changeText: s.fed_latest_move_bps != null ? `${signed(s.fed_latest_move_bps, " bp")} latest move` : "No recent change found",
      foot: `Since ${shortDate(s.fed_move_effective_date)}, EFFR ${pct(s.effr)}`,
      tip: "The FOMC's target range for overnight lending. The move is measured against the previous distinct range, not yesterday.",
    },
    {
      name: "2Y Treasury", value: pct(s.treasury_2y), change: s.treasury_2y_change_bps,
      changeText: signed(s.treasury_2y_change_bps, " bp"), foot: `H.15, ${shortDate(od.DGS2)}`,
      tip: "Sensitive to expectations for the Fed's policy rate over the next couple of years.",
    },
    {
      name: "10Y Treasury", value: pct(s.treasury_10y), change: s.treasury_10y_change_bps,
      changeText: signed(s.treasury_10y_change_bps, " bp"), foot: `H.15, ${shortDate(od.DGS10)}`,
      tip: "The benchmark long-term yield. It feeds discount rates, mortgage rates and equity valuations.",
    },
    {
      name: "10Y breakeven", value: pct(s.breakeven_10y), change: s.breakeven_change_bps,
      changeText: signed(s.breakeven_change_bps, " bp"), foot: `Nominal − TIPS, ${shortDate(od.T10YIE)}`,
      tip: "Market-implied average inflation over ten years: the gap between nominal and inflation-protected Treasury yields.",
    },
    {
      name: "WTI crude", value: s.wti != null ? `$${fixed(s.wti)}` : "–", change: s.wti_change_pct,
      changeText: signed(s.wti_change_pct, "%", 2), foot: `Spot, ${shortDate(od.DCOILWTICO)}`,
      tip: "US crude benchmark. Oil shocks move headline inflation and, through it, rate expectations. FRED's WTI series often lags a few days.",
    },
    {
      name: "VIX", value: fixed(s.vix), change: s.vix_change_points,
      changeText: signed(s.vix_change_points, " pts", 2), foot: `S&P 500 ${signed(s.sp500_change_pct, "%", 2)}, ${shortDate(od.VIXCLS)}`,
      tip: "Option-implied expected volatility of the S&P 500 over the next 30 days.",
    },
  ];

  return (
    <section className="strip" aria-label="Key indicators">
      {items.map((m) => (
        <div className="metric" key={m.name}>
          <div className="metric-name">{m.name} <Tip text={m.tip} label={m.name} /></div>
          <div className="metric-value">{m.value}</div>
          <div className={`metric-change ${dir(m.change)}`}>
            <span aria-hidden="true">{arrow(m.change)}</span> {m.changeText}
          </div>
          <div className="metric-foot">{m.foot}</div>
        </div>
      ))}
    </section>
  );
}
