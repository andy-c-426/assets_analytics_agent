import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { analyzeAsset } from '../api/client';
import { loadSettings } from './SettingsDialog';
import type { AnalysisResponse } from '../api/types';
import styles from './AnalyzePanel.module.css';

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
    <div className={styles.panel}>
      <div className={styles.actions}>
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className={styles.btnAnalyze}
        >
          {loading ? 'Analyzing...' : 'Analyze with AI'}
        </button>
        <button onClick={onOpenSettings} className={styles.btnSettings}>
          LLM Settings
        </button>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {result && (
        <div className={styles.result}>
          <div className={styles.resultMeta}>
            Analysis by {result.model_used} · {result.context_sent.news_count} news articles
          </div>
          <div className={styles.resultContent}>
            <ReactMarkdown>{result.analysis}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
