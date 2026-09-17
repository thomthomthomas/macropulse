"use client";

import { useMemo, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { RatePoint } from "@/lib/types";

const RANGES = { "1M": 31, "3M": 92, "6M": 183, "1Y": 366 } as const;
type Range = keyof typeof RANGES;

const tick = (d: string) =>
  new Date(d + "T00:00:00Z").toLocaleDateString("en-SG", { day: "numeric", month: "short", timeZone: "UTC" });

export default function RatesChart({ data }: { data: RatePoint[] }) {
  const [range, setRange] = useState<Range>("6M");

  const shown = useMemo(() => {
    if (!data.length) return [];
    const last = new Date(data[data.length - 1].date + "T00:00:00Z");
    last.setUTCDate(last.getUTCDate() - RANGES[range]);
    const cut = last.toISOString().slice(0, 10);
    return data.filter((p) => p.date >= cut);
  }, [data, range]);

  if (!data.length) return <p className="quiet">No yield history yet. It fills in after the first update run.</p>;

  return (
    <div>
      <div className="sec-head" style={{ marginBottom: 8 }}>
        <div className="legend">
          <span><i style={{ background: "var(--up)" }} />2Y</span>
          <span><i style={{ background: "var(--down)" }} />10Y</span>
        </div>
        <div className="tabs" role="group" aria-label="Chart range">
          {(Object.keys(RANGES) as Range[]).map((r) => (
            <button key={r} type="button" aria-pressed={r === range} onClick={() => setRange(r)}>{r}</button>
          ))}
        </div>
      </div>
      <div style={{ width: "100%", height: 300 }}>
        <ResponsiveContainer>
          <LineChart data={shown} margin={{ top: 6, right: 8, left: -12, bottom: 0 }}>
            <CartesianGrid stroke="#262b31" vertical={false} />
            <XAxis dataKey="date" tickFormatter={tick} stroke="#8b949e" fontSize={12} tickLine={false}
              axisLine={{ stroke: "#262b31" }} minTickGap={40} />
            <YAxis domain={["auto", "auto"]} stroke="#8b949e" fontSize={12} tickLine={false} axisLine={false}
              tickFormatter={(v: number) => `${v.toFixed(2)}%`} width={58} />
            <Tooltip
              contentStyle={{ background: "#1d2127", border: "1px solid #262b31", fontSize: 13 }}
              labelStyle={{ color: "#8b949e" }}
              labelFormatter={(d) => tick(String(d))}
              formatter={(v, name) => [`${Number(v).toFixed(2)}%`, name === "y2" ? "2Y" : "10Y"]}
            />
            <Line type="monotone" dataKey="y2" stroke="#e0a84e" strokeWidth={1.75} dot={false} connectNulls isAnimationActive={false} />
            <Line type="monotone" dataKey="y10" stroke="#6fa3d8" strokeWidth={1.75} dot={false} connectNulls isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
