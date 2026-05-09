import type { NewsArticle } from '../api/types';
import styles from './NewsList.module.css';

export default function NewsList({ news }: { news: NewsArticle[] }) {
  if (news.length === 0) return null;

  return (
    <div className={styles.card}>
      <h3 className={styles.sectionTitle}>Recent News</h3>
      <div className={styles.list}>
        {news.map((article, i) => (
          <a
            key={i}
            href={article.link || '#'}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.article}
          >
            <div className={styles.articleTitle}>{article.title}</div>
            <div className={styles.articleMeta}>
              {article.publisher && <span>{article.publisher}</span>}
              {article.published_at && <span>{formatDate(article.published_at)}</span>}
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}

function formatDate(ts: string): string {
  try {
    const d = new Date(Number(ts) * 1000);
    return d.toLocaleDateString();
  } catch {
    return ts;
  }
}
