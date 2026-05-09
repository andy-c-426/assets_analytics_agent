import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getAssetDetail } from '../api/client';
import AssetDetailComponent from '../components/AssetDetail';
import PriceChart from '../components/PriceChart';
import NewsList from '../components/NewsList';
import SettingsDialog from '../components/SettingsDialog';
import AnalyzePanel from '../components/AnalyzePanel';
import Skeleton from '../components/Skeleton';
import type { AssetDetail, AnalysisRequest } from '../api/types';
import styles from './AssetPage.module.css';

export default function AssetPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const [asset, setAsset] = useState<AssetDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [, setSettings] = useState<AnalysisRequest | null>(null);

  useEffect(() => {
    if (!symbol) return;
    setLoading(true);
    setError(null);
    getAssetDetail(symbol)
      .then(setAsset)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [symbol]);

  if (loading) {
    return (
      <div className={styles.skeleton}>
        <Skeleton height={20} width={120} style={{ marginBottom: 24 }} />
        <Skeleton height={180} style={{ marginBottom: 24 }} borderRadius={12} />
        <Skeleton height={340} style={{ marginBottom: 24 }} borderRadius={12} />
        <Skeleton height={200} borderRadius={12} />
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.page}>
        <Link to="/" className={styles.backLink}>&larr; Back to search</Link>
        <div style={{ padding: 24, background: 'var(--red-subtle)', color: 'var(--red)', borderRadius: 'var(--radius-md)', fontSize: 14 }}>
          Error: {error}
        </div>
      </div>
    );
  }

  if (!asset) return null;

  return (
    <div className={styles.page}>
      <Link to="/" className={styles.backLink}>&larr; Back to search</Link>
      <AssetDetailComponent asset={asset} />
      <PriceChart symbol={asset.symbol} />
      <NewsList news={asset.news} />
      <AnalyzePanel symbol={asset.symbol} onOpenSettings={() => setSettingsOpen(true)} />
      <SettingsDialog
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onSaved={setSettings}
      />
    </div>
  );
}
