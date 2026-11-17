import type {
  Industry,
  IndustryDetailResponse,
  OverviewResponse,
  PricesResponse,
  SyncJob,
  VersionInfo,
} from './types';

async function get<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}: ${await res.text()}`);
  }
  return (await res.json()) as T;
}

async function post<T>(url: string): Promise<T> {
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}: ${await res.text()}`);
  }
  return (await res.json()) as T;
}

export const api = {
  version: () => get<VersionInfo>('/api/data/version'),
  industries: () => get<Industry[]>('/api/industries'),
  overview: () => get<OverviewResponse>('/api/overview'),
  industry: (code: string) => get<IndustryDetailResponse>(`/api/industries/${code}`),
  prices: (codes: string[], start = '2024-01') =>
    get<PricesResponse>(`/api/prices?codes=${encodeURIComponent(codes.join(','))}&start=${start}`),
  sync: () => post<{ jobId: string; status: string; reused: boolean }>('/api/sync?trigger=page'),
  syncJob: (id: string) => get<SyncJob>(`/api/sync/${id}`),
};
