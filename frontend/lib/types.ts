export type Signal = {
  factor: string;
  direction: "up" | "down";
  value: number;
  unit: "bp" | "%" | "pts";
  interpretation: string;
  key: "rates2y" | "rates10y" | "inflation" | "oil" | "vix" | "equities";
  news_support?: { title: string; url: string; domain: string }[];
};

export type Regime = {
  rates: string; inflation: string; oil: string; volatility: string; equities: string;
};

export type Snapshot = {
  snapshot_date: string;
  fed_lower: number | null; fed_upper: number | null; fed_midpoint: number | null;
  fed_latest_move_bps: number | null; fed_move_effective_date: string | null;
  effr: number | null;
  treasury_2y: number | null; treasury_2y_change_bps: number | null;
  treasury_10y: number | null; treasury_10y_change_bps: number | null;
  curve_2s10s_bps: number | null;
  breakeven_10y: number | null; breakeven_change_bps: number | null;
  wti: number | null; wti_change_pct: number | null;
  vix: number | null; vix_change_points: number | null;
  sp500: number | null; sp500_change_pct: number | null;
  observation_dates: Record<string, string | null> | null;
  signals: Signal[] | null;
  regime: Regime | null;
  summary: string | null;
  generated_at: string;
};

export type Article = {
  id?: number; title: string; url: string; domain: string | null;
  published_at: string | null; topic: string | null; score: number | null;
};

export type RatePoint = { date: string; y2?: number; y10?: number };

export type Dashboard = {
  snapshot: Snapshot | null;
  news: Article[];
  rates: RatePoint[];
  mode: "live" | "demo" | "error";
  error?: string;
};
