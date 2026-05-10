import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { getPriceHistory } from '../api/client';
import { useLocale } from '../i18n/LocaleContext';
import type { OHLCV } from '../api/types';
import styles from './PriceChart.module.css';

const PERIODS = [
  { label: '1M', value: '1mo' },
  { label: '6M', value: '6mo' },
  { label: '1Y', value: '1y' },
  { label: '5Y', value: '5y' },
  { label: 'Max', value: 'max' },
];

export default function PriceChart({ symbol }: { symbol: string }) {
  const { t } = useLocale();
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
    <div className={styles.card}>
      <div className={styles.header}>
        <h3 className={styles.sectionTitle}>{t('chart.title')}</h3>
        <div className={styles.periods}>
          {PERIODS.map((p) => (
            <button
              key={p.value}
              onClick={() => setPeriod(p.value)}
              className={`${styles.periodBtn} ${period === p.value ? styles.periodBtnActive : ''}`}
            >
              {t(`chart.${p.label}`)}
            </button>
          ))}
        </div>
      </div>
      {loading ? (
        <div className={styles.empty}>{t('chart.loading')}</div>
      ) : chartData.length === 0 ? (
        <div className={styles.empty}>{t('chart.noData')}</div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
            <XAxis dataKey="date" fontSize={11} tick={{ fill: 'var(--text-muted)' }} />
            <YAxis fontSize={11} tick={{ fill: 'var(--text-muted)' }} domain={['auto', 'auto']} />
            <Tooltip
              contentStyle={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-sm)',
                fontFamily: 'var(--font-mono)',
                fontSize: 13,
              }}
            />
            <Line type="monotone" dataKey="price" stroke="var(--accent)" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
