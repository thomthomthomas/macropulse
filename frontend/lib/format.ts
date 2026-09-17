const n = (v: number | null | undefined, d = 2) =>
  v === null || v === undefined || Number.isNaN(Number(v)) ? "–" : Number(v).toFixed(d);

export const pct = (v: number | null | undefined) => (v == null ? "–" : `${n(v)}%`);

export function signed(v: number | null | undefined, unit: string, d = 0) {
  if (v === null || v === undefined) return "–";
  const x = Number(v);
  const s = x > 0 ? "+" : x < 0 ? "−" : "±";
  return `${s}${Math.abs(x).toFixed(d)}${unit}`;
}

export function dir(v: number | null | undefined): "up" | "down" | "flat" {
  if (v === null || v === undefined || Number(v) === 0) return "flat";
  return Number(v) > 0 ? "up" : "down";
}

export const arrow = (v: number | null | undefined) =>
  ({ up: "▲", down: "▼", flat: "■" })[dir(v)];

export function shortDate(iso: string | null | undefined) {
  if (!iso) return "–";
  const d = new Date(iso.length === 10 ? iso + "T00:00:00Z" : iso);
  return d.toLocaleDateString("en-SG", { day: "numeric", month: "short", timeZone: "UTC" });
}

export function longDate(iso: string | null | undefined) {
  if (!iso) return "–";
  return new Date(iso + "T00:00:00Z").toLocaleDateString("en-SG", {
    weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC",
  });
}

export function sgtTime(iso: string | null | undefined) {
  if (!iso) return "–";
  return new Date(iso).toLocaleString("en-SG", {
    day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
    hour12: false, timeZone: "Asia/Singapore",
  }) + " SGT";
}

export { n as fixed };
