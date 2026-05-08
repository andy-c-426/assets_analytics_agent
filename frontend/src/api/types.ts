export interface AssetSearchResult {
  symbol: string;
  name: string;
  exchange: string;
  type: string;
  market: string;
  currency: string;
}

export interface AssetProfile {
  name: string;
  sector?: string;
  industry?: string;
  market_cap?: number;
  description?: string;
  country?: string;
  website?: string;
}

export interface PriceData {
  current: number;
  previous_close?: number;
  open?: number;
  high?: number;
  low?: number;
  change?: number;
  change_pct?: number;
  currency: string;
}

export interface KeyMetrics {
  pe_ratio?: number;
  pb_ratio?: number;
  eps?: number;
  dividend_yield?: number;
  beta?: number;
  fifty_two_week_high?: number;
  fifty_two_week_low?: number;
}

export interface NewsArticle {
  title: string;
  publisher?: string;
  link?: string;
  published_at?: string;
  summary?: string;
}

export interface AssetDetail {
  symbol: string;
  profile: AssetProfile;
  price: PriceData;
  metrics: KeyMetrics;
  news: NewsArticle[];
}

export interface OHLCV {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface AnalysisRequest {
  provider: string;
  model: string;
  api_key: string;
  base_url?: string;
}

export interface AnalysisResponse {
  symbol: string;
  analysis: string;
  model_used: string;
  context_sent: {
    data_points: number;
    news_count: number;
  };
}
