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

export function getAssetDetail(symbol: string, finnhubKey?: string): Promise<AssetDetail> {
  const params = new URLSearchParams();
  if (finnhubKey) params.set('finnhub_key', finnhubKey);
  const qs = params.toString();
  return get<AssetDetail>(`/assets/${encodeURIComponent(symbol)}${qs ? `?${qs}` : ''}`);
}

export function getPriceHistory(symbol: string, period: string): Promise<OHLCV[]> {
  return get<OHLCV[]>(`/assets/${encodeURIComponent(symbol)}/price-history?period=${period}`);
}

export interface DataWidgetResult {
  symbol: string;
  data: string;
}

export function getMarketData(symbol: string): Promise<DataWidgetResult> {
  return get<DataWidgetResult>(`/assets/${encodeURIComponent(symbol)}/market-data`);
}

export function getMacroResearch(symbol: string): Promise<DataWidgetResult> {
  return get<DataWidgetResult>(`/assets/${encodeURIComponent(symbol)}/macro-research`);
}

export function getSentimentNews(symbol: string, finnhubKey?: string): Promise<DataWidgetResult> {
  const params = new URLSearchParams();
  if (finnhubKey) params.set('finnhub_api_key', finnhubKey);
  const qs = params.toString();
  return get<DataWidgetResult>(`/assets/${encodeURIComponent(symbol)}/sentiment-news${qs ? `?${qs}` : ''}`);
}

export function getCapitalFlow(symbol: string): Promise<DataWidgetResult> {
  return get<DataWidgetResult>(`/assets/${encodeURIComponent(symbol)}/capital-flow`);
}

export function getCnSentiment(symbol: string): Promise<DataWidgetResult> {
  return get<DataWidgetResult>(`/assets/${encodeURIComponent(symbol)}/cn-sentiment`);
}

export function getUsFundamentals(symbol: string): Promise<DataWidgetResult> {
  return get<DataWidgetResult>(`/assets/${encodeURIComponent(symbol)}/us-fundamentals`);
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
