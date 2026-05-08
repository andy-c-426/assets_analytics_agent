import { useState } from 'react';
import type { AnalysisRequest } from '../api/types';

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

  if (!open) return null;

  function handleSave() {
    const settings: AnalysisRequest = { provider, model, api_key: apiKey, base_url: baseUrl || undefined };
    saveSettings(settings);
    onSaved(settings);
    onClose();
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100,
    }} onClick={onClose}>
      <div style={{
        background: 'white', borderRadius: 12, padding: 28, maxWidth: 420, width: '90%',
        boxShadow: '0 8px 30px rgba(0,0,0,0.2)',
      }} onClick={(e) => e.stopPropagation()}>
        <h3 style={{ margin: '0 0 20px', fontSize: 20 }}>LLM Settings</h3>

        <label style={labelStyle}>Provider</label>
        <select value={provider} onChange={(e) => setProvider(e.target.value)} style={inputStyle}>
          {PROVIDERS.map((p) => (
            <option key={p.value} value={p.value}>{p.label}</option>
          ))}
        </select>

        <label style={labelStyle}>Model Name</label>
        <input
          type="text" value={model} onChange={(e) => setModel(e.target.value)}
          placeholder={provider === 'claude' ? 'claude-sonnet-4-6' : provider === 'openai' ? 'gpt-4o' : 'deepseek-chat'}
          style={inputStyle}
        />

        <label style={labelStyle}>API Key</label>
        <input
          type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)}
          placeholder="sk-..."
          style={inputStyle}
        />

        <label style={labelStyle}>Base URL (optional)</label>
        <input
          type="text" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)}
          placeholder={provider === 'deepseek' ? 'https://api.deepseek.com/v1' : 'Leave empty for default'}
          style={inputStyle}
        />

        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 20 }}>
          <button onClick={onClose} style={{ ...btnStyle, background: '#eee', color: '#555' }}>Cancel</button>
          <button
            onClick={handleSave}
            disabled={!model || !apiKey}
            style={{ ...btnStyle, background: !model || !apiKey ? '#ccc' : '#1976d2', color: 'white' }}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}

const labelStyle: React.CSSProperties = { display: 'block', fontSize: 13, fontWeight: 500, marginBottom: 4, marginTop: 12 };

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid #ddd',
  fontSize: 14, boxSizing: 'border-box', outline: 'none',
};

const btnStyle: React.CSSProperties = {
  padding: '8px 20px', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14, fontWeight: 500,
};
