import { useState } from 'react';
import type { AnalysisRequest } from '../api/types';
import styles from './SettingsDialog.module.css';

const STORAGE_KEY = 'llm_settings';

export function loadSettings(): AnalysisRequest | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

function saveSettings(settings: AnalysisRequest) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: (s: AnalysisRequest) => void;
}

const PROVIDERS = [
  { value: 'claude', label: 'Claude (Anthropic)' },
  { value: 'openai', label: 'GPT (OpenAI)' },
  { value: 'deepseek', label: 'DeepSeek' },
];

export default function SettingsDialog({ open, onClose, onSaved }: Props) {
  const existing = loadSettings();
  const [provider, setProvider] = useState(existing?.provider || 'claude');
  const [model, setModel] = useState(existing?.model || '');
  const [apiKey, setApiKey] = useState(existing?.api_key || '');
  const [baseUrl, setBaseUrl] = useState(existing?.base_url || '');
  const [finnhubKey, setFinnhubKey] = useState(existing?.finnhub_api_key || '');

  if (!open) return null;

  function handleSave() {
    const settings: AnalysisRequest = { provider, model, api_key: apiKey, base_url: baseUrl || undefined, finnhub_api_key: finnhubKey || undefined };
    saveSettings(settings);
    onSaved(settings);
    onClose();
  }

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <h3 className={styles.title}>LLM Settings</h3>

        <label className={styles.label}>Provider</label>
        <select value={provider} onChange={(e) => setProvider(e.target.value)} className={styles.select}>
          {PROVIDERS.map((p) => (
            <option key={p.value} value={p.value}>{p.label}</option>
          ))}
        </select>

        <label className={styles.label}>Model Name</label>
        <input
          type="text" value={model} onChange={(e) => setModel(e.target.value)}
          placeholder={provider === 'claude' ? 'claude-sonnet-4-6' : provider === 'openai' ? 'gpt-4o' : 'deepseek-chat'}
          className={styles.input}
        />

        <label className={styles.label}>API Key</label>
        <input
          type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)}
          placeholder="sk-..."
          className={styles.input}
        />

        <label className={styles.label}>Base URL (optional)</label>
        <input
          type="text" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)}
          placeholder={provider === 'deepseek' ? 'https://api.deepseek.com/v1' : 'Leave empty for default'}
          className={styles.input}
        />

        <label className={styles.label}>Finnhub API Key (optional — for news)</label>
        <input
          type="password" value={finnhubKey} onChange={(e) => setFinnhubKey(e.target.value)}
          placeholder="Free key from https://finnhub.io/register"
          className={styles.input}
        />

        <div className={styles.actions}>
          <button onClick={onClose} className={styles.btnCancel}>Cancel</button>
          <button
            onClick={handleSave}
            disabled={!model || !apiKey}
            className={styles.btnSave}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
