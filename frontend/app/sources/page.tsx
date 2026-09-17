import Link from "next/link";

const ROWS = [
  ["DFEDTARL / DFEDTARU", "Federal funds target range, lower and upper limits", "Board of Governors of the Federal Reserve System"],
  ["DFF", "Effective federal funds rate", "Federal Reserve Bank of New York via H.15"],
  ["DGS2 / DGS10", "2- and 10-year Treasury constant maturity yields", "Federal Reserve H.15"],
  ["T10YIE", "10-year breakeven inflation rate", "Federal Reserve Bank of St. Louis"],
  ["DCOILWTICO", "WTI crude oil spot price, Cushing OK", "U.S. Energy Information Administration"],
  ["VIXCLS", "CBOE Volatility Index", "Cboe Exchange, Inc."],
  ["SP500", "S&P 500 index", "S&P Dow Jones Indices LLC"],
];

export default function Sources() {
  return (
    <main className="wrap">
      <header className="masthead">
        <div className="brand">MacroPulse <span>Data sources</span></div>
        <Link href="/" className="masthead-meta">Back to dashboard</Link>
      </header>
      <section className="sec">
        <table className="table">
          <thead><tr><th>FRED series</th><th>What it is</th><th>Original source</th></tr></thead>
          <tbody>
            {ROWS.map(([id, what, src]) => (
              <tr key={id}>
                <td><a href={`https://fred.stlouisfed.org/series/${id.split(" ")[0]}`} target="_blank" rel="noopener noreferrer">{id}</a></td>
                <td>{what}</td><td>{src}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="sec-note" style={{ marginTop: 16, maxWidth: "70ch" }}>
          Data is retrieved through the FRED API, Federal Reserve Bank of St. Louis. Some series carry their own copyright and usage terms; check each series&apos; notes before commercial use. News comes from the GDELT DOC 2.0 API. Only headlines, publisher and links are stored; article text is never copied.
        </p>
      </section>
    </main>
  );
}
