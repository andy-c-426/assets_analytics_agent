import type {
  AssetSearchResult,
  AssetDetail,
  OHLCV,
  AnalysisRequest,
  AnalysisResponse,
} from './types';

const BASE = '/api';

async function get<T>(url: string): Promise<T> {
  const res = await fetch(`${BASE}${url}`);
  if (!res.ok) throw new Error(`GET ${url} failed: ${res.status}`);
  return res.json();
}

async function post<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${url} failed: ${res.status}`);
  return res.json();
}

export function searchAssets(q: string): Promise<AssetSearchResult[]> {
  return get<AssetSearchResult[]>(`/search?q=${encodeURIComponent(q)}`);
}

export function getAssetDetail(symbol: string): Promise<AssetDetail> {
  return get<AssetDetail>(`/assets/${encodeURIComponent(symbol)}`);
}

export function getPriceHistory(symbol: string, period: string): Promise<OHLCV[]> {
  return get<OHLCV[]>(`/assets/${encodeURIComponent(symbol)}/price-history?period=${period}`);
}

export function analyzeAsset(
  symbol: string,
  config: AnalysisRequest
): Promise<AnalysisResponse> {
  return post<AnalysisResponse>(`/analyze/${encodeURIComponent(symbol)}`, config);
}

export async function analyzeAssetStream(
  symbol: string,
  config: AnalysisRequest,
  signal?: AbortSignal
): Promise<ReadableStream<Uint8Array>> {
  const res = await fetch(`${BASE}/analyze/${encodeURIComponent(symbol)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
    signal,
  });
  if (!res.ok) throw new Error(`POST /analyze failed: ${res.status}`);
  if (!res.body) throw new Error('No response body');
  return res.body;
}
