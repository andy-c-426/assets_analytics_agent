import type { NewsArticle } from '../api/types';

export default function NewsList({ news }: { news: NewsArticle[] }) {
  if (news.length === 0) return null;

  return (
    <div style={{ marginBottom: 24 }}>
      <h3 style={{ fontSize: 18, marginBottom: 12 }}>Recent News</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {news.map((article, i) => (
          <a
            key={i}
            href={article.link || '#'}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              textDecoration: 'none', color: 'inherit',
              padding: '12px 14px', borderRadius: 8, border: '1px solid #eee',
              display: 'block',
            }}
          >
            <div style={{ fontWeight: 500, fontSize: 14, marginBottom: 3 }}>{article.title}</div>
            <div style={{ display: 'flex', gap: 10, fontSize: 12, color: '#888' }}>
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
