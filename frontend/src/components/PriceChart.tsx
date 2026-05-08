import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { getPriceHistory } from '../api/client';
import type { OHLCV } from '../api/types';

const PERIODS = [
  { label: '1M', value: '1mo' },
  { label: '6M', value: '6mo' },
  { label: '1Y', value: '1y' },
  { label: '5Y', value: '5y' },
  { label: 'Max', value: 'max' },
];

export default function PriceChart({ symbol }: { symbol: string }) {
  const [period, setPeriod] = useState('1mo');
  const [data, setData] = useState<OHLCV[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getPriceHistory(symbol, period)
      .then(setData)
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, [symbol, period]);

  const chartData = data.map((d) => ({ date: d.date, price: d.close }));

  return (
    <div style={{ marginBottom: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h3 style={{ margin: 0, fontSize: 18 }}>Price History</h3>
        <div style={{ display: 'flex', gap: 4 }}>
          {PERIODS.map((p) => (
            <button
              key={p.value}
              onClick={() => setPeriod(p.value)}
              style={{
                padding: '4px 12px', border: '1px solid #ddd', borderRadius: 6,
                background: period === p.value ? '#1976d2' : 'white',
                color: period === p.value ? 'white' : '#555',
                cursor: 'pointer', fontSize: 13, fontWeight: 500,
              }}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>
      {loading ? (
        <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>Loading chart...</div>
      ) : chartData.length === 0 ? (
        <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>No price data available</div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" fontSize={11} tick={{ fill: '#888' }} />
            <YAxis fontSize={11} tick={{ fill: '#888' }} domain={['auto', 'auto']} />
            <Tooltip />
            <Line type="monotone" dataKey="price" stroke="#1976d2" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
