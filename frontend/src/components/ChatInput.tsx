import { useState, useRef, useEffect } from 'react';
import styles from './ChatInput.module.css';

interface Props {
  onSend: (message: string) => void;
  onStop?: () => void;
  loading?: boolean;
  placeholder?: string;
}

export default function ChatInput({ onSend, onStop, loading, placeholder }: Props) {
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 120) + 'px';
    }
  }, [value]);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || loading) return;
    onSend(trimmed);
    setValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className={styles.inputBar}>
      <textarea
        ref={inputRef}
        className={styles.textarea}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder || 'Ask about any stock... (Shift+Enter for newline)'}
        rows={1}
        disabled={loading}
      />
      <div className={styles.buttons}>
        {loading ? (
          <button className={styles.stopBtn} onClick={onStop}>
            Stop
          </button>
        ) : (
          <button
            className={styles.sendBtn}
            onClick={handleSend}
            disabled={!value.trim()}
          >
            Send
          </button>
        )}
      </div>
    </div>
  );
}
