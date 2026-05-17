import { useState, useRef, useCallback, useEffect } from 'react';
import { postChat, type ChatDirection } from '../api/client';
import { loadSettings } from '../components/SettingsDialog';
import ChatMessage from '../components/ChatMessage';
import ChatInput from '../components/ChatInput';
import SettingsDialog from '../components/SettingsDialog';
import { useLocale } from '../i18n/LocaleContext';
import type { AnalysisRequest } from '../api/types';
import styles from './ChatPage.module.css';

interface Message {
  id: number;
  type: 'text' | 'asset_card' | 'analysis_stream' | 'clarification' | 'error' | 'loading';
  role: 'user' | 'assistant' | 'system';
  content?: string;
  symbol?: string;
  report?: string;
  choices?: string[];
}

let msgId = 0;

export default function ChatPage() {
  const { t, locale } = useLocale();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settings, setSettings] = useState<AnalysisRequest | null>(loadSettings);
  const directionRef = useRef<ChatDirection | null>(null);
  const historyRef = useRef<{ role: 'user' | 'assistant'; content: string }[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addMessage = useCallback((msg: Omit<Message, 'id'>) => {
    const id = ++msgId;
    setMessages((prev) => [...prev, { ...msg, id }]);
    return id;
  }, []);

  const updateMessage = useCallback((id: number, updates: Partial<Message>) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, ...updates } : m)));
  }, []);

  const removeMessage = useCallback((id: number) => {
    setMessages((prev) => prev.filter((m) => m.id !== id));
  }, []);

  const handleSend = useCallback(async (message: string) => {
    const currentSettings = settings || loadSettings();
    if (!currentSettings) {
      setSettingsOpen(true);
      return;
    }

    addMessage({ type: 'text', role: 'user', content: message });
    historyRef.current.push({ role: 'user', content: message });

    setLoading(true);
    const loadingId = addMessage({ type: 'loading', role: 'assistant' });

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const body = await postChat({
        message,
        history: historyRef.current.slice(0, -1),
        direction: directionRef.current,
        user_preferences: {
          language: locale,
          llm_config: {
            provider: currentSettings.provider,
            model: currentSettings.model,
            api_key: currentSettings.api_key,
            base_url: currentSettings.base_url,
          },
          finnhub_api_key: currentSettings.finnhub_api_key,
        },
      }, controller.signal);

      removeMessage(loadingId);

      const reader = body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let currentStreamId: number | null = null;
      let streamBuffer = '';

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

              switch (eventType) {
                case 'clarification':
                  directionRef.current = data.direction;
                  addMessage({
                    type: 'clarification',
                    role: 'assistant',
                    content: data.message,
                    choices: extractChoices(data.message),
                  });
                  historyRef.current.push({ role: 'assistant', content: data.message });
                  break;

                case 'proposal':
                  directionRef.current = data.direction;
                  addMessage({ type: 'text', role: 'assistant', content: data.message });
                  historyRef.current.push({ role: 'assistant', content: data.message });
                  break;

                case 'asset_card':
                  addMessage({
                    type: 'asset_card',
                    role: 'assistant',
                    symbol: data.symbol,
                  });
                  break;

                case 'tool_start':
                  break;

                case 'tool_result':
                  break;

                case 'reasoning_chunk':
                  streamBuffer += data.text || '';
                  if (!currentStreamId) {
                    currentStreamId = addMessage({
                      type: 'analysis_stream',
                      role: 'assistant',
                      report: streamBuffer,
                    });
                  } else {
                    updateMessage(currentStreamId, { report: streamBuffer });
                  }
                  break;

                case 'report_ready':
                  streamBuffer = data.report || '';
                  if (currentStreamId) {
                    updateMessage(currentStreamId, {
                      type: 'analysis_stream',
                      report: streamBuffer,
                    });
                  } else {
                    addMessage({
                      type: 'analysis_stream',
                      role: 'assistant',
                      report: streamBuffer,
                    });
                  }
                  historyRef.current.push({ role: 'assistant', content: streamBuffer.slice(0, 200) });
                  streamBuffer = '';
                  currentStreamId = null;
                  break;

                case 'comparison':
                  addMessage({
                    type: 'text',
                    role: 'assistant',
                    content: data.message,
                  });
                  break;

                case 'text':
                  addMessage({ type: 'text', role: 'assistant', content: data.message });
                  historyRef.current.push({ role: 'assistant', content: data.message });
                  break;

                case 'error':
                  addMessage({ type: 'error', role: 'assistant', content: data.message });
                  break;

                case 'done':
                  break;
              }
            } catch { /* skip malformed JSON */ }
            eventType = '';
          }
        }
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return;
      removeMessage(loadingId);
      addMessage({
        type: 'error',
        role: 'assistant',
        content: err instanceof Error ? err.message : 'Chat failed',
      });
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  }, [settings, locale, addMessage, updateMessage, removeMessage]);

  const handleStop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const handleSettingsSaved = useCallback((s: AnalysisRequest) => {
    setSettings(s);
  }, []);

  return (
    <div className={styles.page}>
      <div className={styles.chatArea}>
        {messages.length === 0 && (
          <div className={styles.welcome}>
            <h2>{t('chat.welcome')}</h2>
            <p>{t('chat.welcomeSub')}</p>
          </div>
        )}
        {messages.map((msg) => (
          <ChatMessage key={msg.id} msg={msg} />
        ))}
        <div ref={chatEndRef} />
      </div>
      <ChatInput
        onSend={handleSend}
        onStop={handleStop}
        loading={loading}
        placeholder={t('chat.placeholder')}
      />
      <SettingsDialog
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onSaved={handleSettingsSaved}
      />
    </div>
  );
}

function extractChoices(text: string): string[] {
  const choices: string[] = [];
  const lines = text.split('\n');
  for (const line of lines) {
    const match = line.match(/^[\d]+[.)]\s*(.+)/);
    if (match) {
      choices.push(match[1].trim());
    }
  }
  return choices;
}
