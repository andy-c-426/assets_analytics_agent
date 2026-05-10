import { useState } from 'react';
import { useLocale } from '../i18n/LocaleContext';
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
  const { t } = useLocale();
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
        <h3 className={styles.title}>{t('settings.title')}</h3>

        <label className={styles.label}>{t('settings.provider')}</label>
        <select value={provider} onChange={(e) => setProvider(e.target.value)} className={styles.select}>
          {PROVIDERS.map((p) => (
            <option key={p.value} value={p.value}>{p.label}</option>
          ))}
        </select>

        <label className={styles.label}>{t('settings.model')}</label>
        <input
          type="text" value={model} onChange={(e) => setModel(e.target.value)}
          placeholder={provider === 'claude' ? 'claude-sonnet-4-6' : provider === 'openai' ? 'gpt-4o' : 'deepseek-chat'}
          className={styles.input}
        />

        <label className={styles.label}>{t('settings.apiKey')}</label>
        <input
          type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)}
          placeholder="sk-..."
          className={styles.input}
        />

        <label className={styles.label}>{t('settings.baseUrl')}</label>
        <input
          type="text" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)}
          placeholder={provider === 'deepseek' ? 'https://api.deepseek.com/v1' : t('settings.baseUrlPlaceholder')}
          className={styles.input}
        />

        <label className={styles.label}>{t('settings.finnhubKey')}</label>
        <input
          type="password" value={finnhubKey} onChange={(e) => setFinnhubKey(e.target.value)}
          placeholder={t('settings.finnhubPlaceholder')}
          className={styles.input}
        />

        <div className={styles.actions}>
          <button onClick={onClose} className={styles.btnCancel}>{t('settings.cancel')}</button>
          <button
            onClick={handleSave}
            disabled={!model || !apiKey}
            className={styles.btnSave}
          >
            {t('settings.save')}
          </button>
        </div>
      </div>
    </div>
  );
}
