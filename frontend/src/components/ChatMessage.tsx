import ReactMarkdown from 'react-markdown';
import { Link } from 'react-router-dom';
import styles from './ChatMessage.module.css';

interface ChatMessageData {
  type: 'text' | 'asset_card' | 'analysis_stream' | 'clarification' | 'error' | 'loading';
  role: 'user' | 'assistant' | 'system';
  content?: string;
  symbol?: string;
  report?: string;
  choices?: string[];
  onChoice?: (choice: string) => void;
}

export default function ChatMessage({ msg }: { msg: ChatMessageData }) {
  const className =
    msg.role === 'user' ? styles.userMsg :
    msg.role === 'system' ? styles.systemMsg :
    styles.assistantMsg;

  const renderContent = () => {
    switch (msg.type) {
      case 'text':
        return <ReactMarkdown>{msg.content || ''}</ReactMarkdown>;

      case 'asset_card':
        return (
          <div className={styles.assetCard}>
            <span className={styles.assetSymbol}>{msg.symbol}</span>
            {msg.report && (
              <Link to={`/asset/${msg.symbol}`} className={styles.assetLink}>
                View Full Analysis →
              </Link>
            )}
          </div>
        );

      case 'analysis_stream':
        return (
          <div className={styles.analysisBlock}>
            <ReactMarkdown>{msg.report || msg.content || ''}</ReactMarkdown>
          </div>
        );

      case 'clarification':
        return (
          <div>
            <p>{msg.content}</p>
            {msg.choices && msg.choices.length > 0 && (
              <div className={styles.choiceRow}>
                {msg.choices.map((c, i) => (
                  <button
                    key={i}
                    className={styles.choiceBtn}
                    onClick={() => msg.onChoice?.(c)}
                  >
                    {c}
                  </button>
                ))}
              </div>
            )}
          </div>
        );

      case 'error':
        return <div className={styles.errorBanner}>{msg.content}</div>;

      case 'loading':
        return <span className={styles.loadingDots}>...</span>;

      default:
        return <p>{msg.content}</p>;
    }
  };

  return (
    <div className={`${styles.message} ${className}`}>
      {msg.role === 'assistant' && <span className={styles.label}>Agent</span>}
      {renderContent()}
    </div>
  );
}
