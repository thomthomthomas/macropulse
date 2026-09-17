import { createClient } from "@supabase/supabase-js";
import { demoDashboard } from "./demo";
import type { Article, Dashboard, RatePoint, Snapshot } from "./types";

function client() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) return null;
  return createClient(url, key, { auth: { persistSession: false } });
}

export async function getDashboard(): Promise<Dashboard> {
  const sb = client();
  if (!sb) return demoDashboard;

  try {
    const since = new Date(Date.now() - 48 * 3600 * 1000).toISOString();
    const [snapRes, newsRes, ratesRes] = await Promise.all([
      sb.from("daily_snapshot").select("*").order("snapshot_date", { ascending: false }).limit(1).maybeSingle(),
      sb.from("news").select("id,title,url,domain,published_at,topic,score")
        .gte("published_at", since)
        .order("score", { ascending: false })
        .order("published_at", { ascending: false })
        .limit(40),
      // newest first, then reversed: fixes "oldest 365 rows" bug
      sb.from("observations").select("series_id,observation_date,value")
        .in("series_id", ["DGS2", "DGS10"])
        .order("observation_date", { ascending: false })
        .limit(800),
    ]);
    if (snapRes.error) throw snapRes.error;
    if (newsRes.error) throw newsRes.error;
    if (ratesRes.error) throw ratesRes.error;

    const byDate = new Map<string, RatePoint>();
    for (const r of ratesRes.data ?? []) {
      const p: RatePoint = byDate.get(r.observation_date) ?? { date: String(r.observation_date) };
      if (r.series_id === "DGS2") p.y2 = Number(r.value);
      else p.y10 = Number(r.value);
      byDate.set(r.observation_date, p);
    }
    const rates = [...byDate.values()].sort((a, b) => a.date.localeCompare(b.date));

    return {
      mode: "live",
      snapshot: (snapRes.data as Snapshot) ?? null,
      news: pickTopNews((newsRes.data ?? []) as Article[]),
      rates,
    };
  } catch (e) {
    return { mode: "error", snapshot: null, news: [], rates: [],
      error: e instanceof Error ? e.message : String(e) };
  }
}

/** Best 8, with at most 3 per topic so one story doesn't swamp the list. */
function pickTopNews(rows: Article[]) {
  const perTopic: Record<string, number> = {};
  const out: Article[] = [];
  for (const a of rows) {
    const t = a.topic ?? "other";
    if ((perTopic[t] ?? 0) >= 3) continue;
    perTopic[t] = (perTopic[t] ?? 0) + 1;
    out.push(a);
    if (out.length === 8) break;
  }
  return out;
}
