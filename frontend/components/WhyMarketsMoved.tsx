import type { Signal, Snapshot } from "@/lib/types";
import { dir, signed } from "@/lib/format";

// Ordered along the transmission path: inflation inputs -> rates -> risk -> equities
const ORDER: Signal["key"][] = ["oil", "inflation", "rates2y", "rates10y", "vix", "equities"];

function fmt(sig: Pick<Signal, "value" | "unit">) {
  return signed(sig.value, sig.unit === "bp" ? " bp" : sig.unit === "pts" ? " pts" : "%", sig.unit === "bp" ? 0 : 2);
}

export default function WhyMarketsMoved({ s }: { s: Snapshot }) {
  const signals = [...(s.signals ?? [])].sort((a, b) => ORDER.indexOf(a.key) - ORDER.indexOf(b.key));

  // Always end the chain on equities so the path has a destination.
  const chain: Signal[] = [...signals];
  if (!chain.some((x) => x.key === "equities") && s.sp500_change_pct != null) {
    chain.push({
      factor: "S&P 500", key: "equities", unit: "%", value: s.sp500_change_pct,
      direction: s.sp500_change_pct >= 0 ? "up" : "down",
      interpretation: "Below the threshold for a notable move.",
    });
  }

  const r = s.regime;

  return (
    <section className="sec" aria-labelledby="why">
      <div className="sec-head">
        <h2 className="sec-title" id="why">Why markets moved</h2>
        <span className="sec-note">Signals fire when a move clears its threshold (rates ±5 bp, oil ±2%, VIX ±1 pt)</span>
      </div>

      <div className="why">
        <div>
          {signals.length === 0 ? (
            <p className="quiet">Nothing cleared its threshold in the latest session. Rates, oil and volatility were quiet.</p>
          ) : (
            <>
              <div className="chain" role="list" aria-label="Possible market transmission">
                {chain.map((sig, i) => (
                  <div key={sig.key} style={{ display: "contents" }}>
                    {i > 0 && <span className="link" aria-hidden="true" style={{ animationDelay: `${i * 110 - 50}ms` }} />}
                    <div role="listitem" className={`node ${dir(sig.value)}`} style={{ animationDelay: `${i * 110}ms` }}>
                      <span className="node-factor">{sig.factor}</span>
                      <span className={`node-move ${dir(sig.value)}`}>{fmt(sig)}</span>
                      <span className="node-text">{sig.interpretation}</span>
                    </div>
                  </div>
                ))}
              </div>
              <p className="chain-caption">Possible market transmission. These moves coincided; the chain does not prove one caused the next.</p>

              <div className="evidence">
                {signals.map((sig) => {
                  const support = sig.news_support ?? [];
                  return (
                    <div className="ev-row" key={sig.key}>
                      <span>{sig.factor}</span>
                      <span className={dir(sig.value)}>{fmt(sig)}</span>
                      <div className="ev-news">
                        <span className={`badge ${support.length ? "yes" : ""}`}>
                          {support.length ? "Supported by news" : "Data signal only"}
                        </span>
                        {support.map((h) => (
                          <div key={h.url}>
                            <a href={h.url} target="_blank" rel="noopener noreferrer">{h.title}</a> ({h.domain})
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>

        <aside className="desk" aria-label="Market interpretation">
          <div className="desk-kicker">Desk read</div>
          <p className="desk-note">{s.summary ?? "Interpretation unavailable."}</p>
          {r && (
            <table className="regime">
              <caption className="sr-only">Today&apos;s regime</caption>
              <tbody>
                {([
                  ["Rates", r.rates], ["Inflation expectations", r.inflation], ["Oil", r.oil],
                  ["Volatility", r.volatility], ["Equities", r.equities],
                ] as const).map(([k, v]) => (
                  <tr key={k}>
                    <td>{k}</td>
                    <td className={/Rising|steepening/.test(v) ? "up" : /Falling|flattening/.test(v) ? "down" : "flat"}>{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <p className="desk-foot">
            2s10s curve {signed(s.curve_2s10s_bps, " bp")}. Generated from the day&apos;s data by fixed rules, then checked against headlines. It describes, it doesn&apos;t forecast.
          </p>
        </aside>
      </div>
    </section>
  );
}
