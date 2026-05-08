// frontend/src/pages/AssetPage.tsx
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getAssetDetail } from '../api/client';
import AssetDetailComponent from '../components/AssetDetail';
import PriceChart from '../components/PriceChart';
import NewsList from '../components/NewsList';
import SettingsDialog from '../components/SettingsDialog';
import AnalyzePanel from '../components/AnalyzePanel';
import type { AssetDetail, AnalysisRequest } from '../api/types';

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

  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: '#999' }}>Loading {symbol}...</div>;
  if (error) return <div style={{ padding: 40, textAlign: 'center', color: '#c62828' }}>Error: {error}</div>;
  if (!asset) return null;

  return (
    <div style={{ maxWidth: 860, margin: '0 auto', padding: '24px 20px 60px' }}>
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
