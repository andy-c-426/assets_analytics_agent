import { useState, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { analyzeAssetStream } from '../api/client';
import { loadSettings } from './SettingsDialog';
import { useLocale } from '../i18n/LocaleContext';
import styles from './AnalyzePanel.module.css';

interface Props {
  symbol: string;
  onOpenSettings: () => void;
  prefetchedData?: Record<string, string>;
}

interface Step {
  step_type: string;
  message: string;
  status: 'pending' | 'active' | 'done';
  detail?: string;
}

function formatStepMessage(step: Step, t: (key: string, vars?: Record<string, string>) => string): string {
  switch (step.step_type) {
    case 'planning': return t('analyze.planning');
    case 'evaluating': return t('analyze.evaluating');
    case 'synthesizing': return t('analyze.synthesizing');
    case 'tool_call': return step.message;
    default: return step.message;
  }
}

function StepIcon({ status }: { status: string }) {
  if (status === 'done') return <span style={{ color: 'var(--green)', fontSize: 12 }}>◆</span>;
  if (status === 'active') return <span style={{ color: 'var(--accent)', fontSize: 12 }}>◇</span>;
  return <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>○</span>;
}

export default function AnalyzePanel({ symbol, onOpenSettings, prefetchedData }: Props) {
  const { t, locale } = useLocale();
  const [steps, setSteps] = useState<Step[]>([]);
  const [report, setReport] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const handleAnalyze = useCallback(async () => {
    const settings = loadSettings();
    if (!settings) {
      onOpenSettings();
      return;
    }

    setLoading(true);
    setError(null);
    setSteps([]);
    setReport(null);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const body = await analyzeAssetStream(symbol, { ...settings, language: locale, prefetched_data: prefetchedData }, controller.signal);
      const reader = body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let eventType = '';
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith('data: ') && eventType) {
            try {
              const data = JSON.parse(line.slice(6));
              handleSSEEvent(eventType, data);
            } catch { /* skip malformed */ }
            eventType = '';
          }
        }
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return;
      setError(err instanceof Error ? err.message : t('analyze.failed'));
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  }, [symbol, onOpenSettings]);

  function handleSSEEvent(eventType: string, data: Record<string, unknown>) {
    switch (eventType) {
      case 'step_started': {
        const step = data.step as string;
        const message = data.message as string;
        setSteps((prev) => {
          const updated = prev.map((s) =>
            s.status === 'active' ? { ...s, status: 'done' as const } : s
          );
          return [...updated, { step_type: step, message, status: 'active' }];
        });
        break;
      }
      case 'plan_reasoning': {
        const text = data.text as string;
        setSteps((prev) =>
          prev.map((s) =>
            s.step_type === 'planning' ? { ...s, detail: text } : s
          )
        );
        break;
      }
      case 'tool_called': {
        const tool = data.tool as string;
        setSteps((prev) => [
          ...prev,
          { step_type: 'tool_call', message: t('analyze.fetchingData', { tool }), status: 'active' },
        ]);
        break;
      }
      case 'tool_result': {
        const tool = data.tool as string;
        const summary = data.summary as string;
        setSteps((prev) =>
          prev.map((s) =>
            s.step_type === 'tool_call' && s.message.includes(tool) && s.status === 'active'
              ? { ...s, status: 'done' as const, detail: summary }
              : s
          )
        );
        break;
      }
      case 'reasoning_chunk':
        break;
      case 'report_ready':
        setReport(data.report as string);
        setSteps((prev) =>
          prev.map((s) =>
            s.status === 'active' ? { ...s, status: 'done' as const } : s
          )
        );
        break;
      case 'error':
        setError(data.message as string);
        break;
      case 'done':
        setLoading(false);
        break;
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
          {loading ? t('analyze.analyzing') : t('analyze.button')}
        </button>
        <button onClick={onOpenSettings} className={styles.btnSettings}>
          {t('analyze.settings')}
        </button>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {steps.length > 0 && (
        <div className={styles.stepList}>
          {steps.map((step, i) => (
            <div
              key={i}
              className={
                step.status === 'done' ? styles.stepDone :
                step.status === 'active' ? styles.stepActive :
                styles.stepPending
              }
            >
              <StepIcon status={step.status} />
              <div className={styles.stepText}>
                <span>{formatStepMessage(step, t)}</span>
                {step.detail && <span className={styles.stepDetail}>{step.detail}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      {report && (
        <div className={styles.result}>
          <div className={styles.resultContent}>
            <ReactMarkdown>{report}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
