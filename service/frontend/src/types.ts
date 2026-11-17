export interface LeaderRef {
  code: string;
  name: string;
  weight: number;
  rank: number;
}

export interface Industry {
  code: string;
  name: string;
  stock_count: number;
  sort_order: number;
  leaders: LeaderRef[];
}

export interface SeriesPoint {
  month: string;
  close: number | null;
  ret: number | null;
  norm: number | null;
}

export interface Metrics {
  base_close: number | null;
  last_close: number | null;
  last_month: string | null;
  months: number;
  cum_return: number | null;
  cagr: number | null;
  mdd: number | null;
  annual_vol: number | null;
  best: { month: string; ret: number } | null;
  worst: { month: string; ret: number } | null;
}

export interface PricedSeries {
  code: string;
  name: string;
  isBenchmark: boolean;
  weight: number | null;
  metrics: Metrics;
  series: SeriesPoint[];
}

export interface PricesResponse {
  months: string[];
  series: PricedSeries[];
  normalize: boolean;
  baseMonth: string;
}

export interface OverviewItem {
  code: string;
  name: string;
  stockCount: number;
  leader: { code: string; name: string; weight: number } | null;
  leaderCumReturn: number | null;
  avgCumReturn: number | null;
  maxCumReturn: number | null;
  minCumReturn: number | null;
}

export interface OverviewResponse {
  industries: OverviewItem[];
  benchmark: { name: string; cumReturn: number | null };
  baseMonth: string;
}

export interface IndustryDetailResponse {
  code: string;
  name: string;
  stockCount: number;
  leaders: Array<LeaderRef & { series: SeriesPoint[]; metrics: Metrics }>;
  benchmark: { name: string; metrics: Metrics; series: SeriesPoint[] };
  avgCumReturn: number | null;
  baseMonth: string;
}

export interface VersionInfo {
  lastTradeDate: string | null;
  expectedTradeDate: string;
  lastSyncAt: string | null;
  needsRefresh: boolean;
  syncing: boolean;
  rows: number;
}

export interface SyncJob {
  jobId: string;
  status: 'running' | 'done' | 'failed';
  trigger?: string;
  startedAt?: string;
  finishedAt?: string;
  addedRows?: number;
  rebuilt?: number;
  done?: number;
  total?: number;
  message?: string;
  error?: string;
  latestDate?: string;
  durationMs?: number;
  reused?: boolean;
}
