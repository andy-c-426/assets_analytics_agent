import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { analyzeAsset } from '../api/client';
import { loadSettings } from './SettingsDialog';
import type { AnalysisResponse } from '../api/types';

interface Props {
  symbol: string;
  onOpenSettings: () => void;
}

export default function AnalyzePanel({ symbol, onOpenSettings }: Props) {
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAnalyze() {
    const settings = loadSettings();
    if (!settings) {
      onOpenSettings();
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await analyzeAsset(symbol, settings);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <button
          onClick={handleAnalyze}
          disabled={loading}
          style={{
            padding: '10px 24px', background: loading ? '#ccc' : '#10b981', color: 'white',
            border: 'none', borderRadius: 8, fontSize: 15, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? 'Analyzing...' : 'Analyze with AI'}
        </button>
        <button
          onClick={onOpenSettings}
          style={{
            padding: '10px 16px', background: 'transparent', border: '1px solid #ddd',
            borderRadius: 8, fontSize: 13, cursor: 'pointer', color: '#666',
          }}
        >
          LLM Settings
        </button>
      </div>

      {error && (
        <div style={{ padding: 12, background: '#fff3f3', color: '#c62828', borderRadius: 8, fontSize: 14, marginBottom: 12 }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ background: '#fafafa', border: '1px solid #eee', borderRadius: 12, padding: 20, marginTop: 8 }}>
          <div style={{ fontSize: 12, color: '#999', marginBottom: 16 }}>
            Analysis by {result.model_used} · {result.context_sent.news_count} news articles
          </div>
          <div style={{ lineHeight: 1.7, fontSize: 14 }}>
            <ReactMarkdown>{result.analysis}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
