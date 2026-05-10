import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import type { Locale } from './translations';
import { t as translate } from './translations';

const STORAGE_KEY = 'locale';

function getInitialLocale(): Locale {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw === 'en' || raw === 'zh-CN') return raw;
  } catch { /* localStorage unavailable */ }
  return 'en';
}

interface LocaleContextValue {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string, vars?: Record<string, string>) => string;
}

const LocaleContext = createContext<LocaleContextValue | null>(null);

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(getInitialLocale);

  useEffect(() => {
    try { localStorage.setItem(STORAGE_KEY, locale); } catch { /* ignore */ }
    document.documentElement.lang = locale;
    document.title = translate(locale, 'app.title');
  }, [locale]);

  function setLocale(l: Locale) {
    setLocaleState(l);
  }

  const value: LocaleContextValue = {
    locale,
    setLocale,
    t: (key: string, vars?: Record<string, string>) => translate(locale, key, vars),
  };

  return (
    <LocaleContext.Provider value={value}>
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale(): LocaleContextValue {
  const ctx = useContext(LocaleContext);
  if (!ctx) throw new Error('useLocale must be used within LocaleProvider');
  return ctx;
}
