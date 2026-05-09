# Frontend Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace inline styles with a CSS Modules + CSS custom properties design system (slate+violet palette, dark/light mode, skeletons, micro-animations).

**Architecture:** CSS custom properties in `tokens.css` define the design tokens. `theme.css` overrides tokens for dark mode via `[data-theme="dark"]`. ThemeContext manages toggle state, persisted to localStorage. Each component gets a `.module.css` file — inline `style={{}}` moves to class names. A shared `Skeleton` component handles loading states. Zero new dependencies.

**Tech Stack:** React 19, TypeScript, Vite 8 (CSS Modules native), CSS custom properties, Google Fonts (Inter + JetBrains Mono)

---

### Task 1: Design Tokens & Global Styles

**Files:**
- Create: `frontend/src/styles/tokens.css`
- Create: `frontend/src/styles/global.css`
- Create: `frontend/src/styles/theme.css`
- Modify: `frontend/index.html`

- [ ] **Step 1: Write tokens.css**

Create `frontend/src/styles/tokens.css`:

```css
/* Design tokens — consumed by all components */
:root {
  /* Colors — light */
  --bg-primary: #f8f9fb;
  --bg-surface: #ffffff;
  --border-default: #e5e7eb;
  --border-subtle: #f0f0f0;
  --text-primary: #111827;
  --text-secondary: #374151;
  --text-muted: #6b7280;
  --accent: #6d5dfc;
  --accent-hover: #5a4de0;
  --accent-subtle: rgba(109, 93, 252, 0.08);
  --green: #10b981;
  --red: #ef4444;
  --red-subtle: #fef2f2;

  /* Typography */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* Spacing (4px grid) */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;

  /* Radii */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;

  /* Shadows */
  --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 8px 30px rgba(0, 0, 0, 0.12);

  /* Transitions */
  --transition-fast: 0.15s ease;
  --transition-base: 0.2s ease;
}
```

- [ ] **Step 2: Write global.css**

Create `frontend/src/styles/global.css`:

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

*,
*::before,
*::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: var(--font-sans);
  background: var(--bg-primary);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  transition: background-color var(--transition-base);
}

a {
  color: inherit;
  text-decoration: none;
}

button {
  font-family: inherit;
}

h1, h2, h3, h4, p {
  margin: 0;
}
```

- [ ] **Step 3: Write theme.css**

Create `frontend/src/styles/theme.css`:

```css
[data-theme='dark'] {
  --bg-primary: #0f1115;
  --bg-surface: #1a1d24;
  --border-default: #272a33;
  --border-subtle: #1f2229;
  --text-primary: #f1f5f9;
  --text-secondary: #cbd5e1;
  --text-muted: #8b949e;
  --accent-subtle: rgba(109, 93, 252, 0.12);
  --red-subtle: rgba(239, 68, 68, 0.1);
  --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.2);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 8px 30px rgba(0, 0, 0, 0.5);
}
```

- [ ] **Step 4: Update index.html title and fonts**

Edit `frontend/index.html` — replace `<title>frontend</title>` with `<title>Asset Analytics</title>`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Asset Analytics</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/styles/ frontend/index.html
git commit -m "feat: add design tokens, global styles, and dark theme overrides"
```

---

### Task 2: Theme Context & Toggle

**Files:**
- Create: `frontend/src/theme/ThemeContext.tsx`
- Create: `frontend/src/theme/ThemeToggle.tsx`

- [ ] **Step 1: Write ThemeContext**

Create `frontend/src/theme/ThemeContext.tsx`:

```tsx
import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextValue {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({ theme: 'light', toggleTheme: () => {} });

export function useTheme() {
  return useContext(ThemeContext);
}

function getInitialTheme(): Theme {
  const stored = localStorage.getItem('theme');
  if (stored === 'dark' || stored === 'light') return stored;
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark';
  return 'light';
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  function toggleTheme() {
    setTheme((t) => (t === 'light' ? 'dark' : 'light'));
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
```

- [ ] **Step 2: Write ThemeToggle**

Create `frontend/src/theme/ThemeToggle.tsx`:

```tsx
import { useTheme } from './ThemeContext';

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
      className="theme-toggle"
    >
      {theme === 'light' ? (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      ) : (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="5" />
          <line x1="12" y1="1" x2="12" y2="3" />
          <line x1="12" y1="21" x2="12" y2="23" />
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
          <line x1="1" y1="12" x2="3" y2="12" />
          <line x1="21" y1="12" x2="23" y2="12" />
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </svg>
      )}
    </button>
  );
}
```

Note: ThemeToggle is a utility component rendered inside the top nav (Task 3). Its styling (border, radius, hover) lives in `App.module.css` via the `.theme-toggle` class.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/theme/
git commit -m "feat: add ThemeContext and ThemeToggle for dark/light mode"
```

---

### Task 3: App Shell & Top Nav

**Files:**
- Create: `frontend/src/App.module.css`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: Write App.module.css**

Create `frontend/src/App.module.css`:

```css
.app {
  min-height: 100vh;
}

.nav {
  position: sticky;
  top: 0;
  z-index: 90;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 var(--space-6);
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-default);
}

.logo {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.3px;
}

.logoAccent {
  color: var(--accent);
}

.navRight {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.themeToggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background: var(--bg-surface);
  color: var(--text-muted);
  cursor: pointer;
  transition: color var(--transition-fast), border-color var(--transition-fast);
}

.themeToggle:hover {
  color: var(--text-primary);
  border-color: var(--text-muted);
}

.pageFade {
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
```

- [ ] **Step 2: Rewrite App.tsx with nav and theme toggle**

Rewrite `frontend/src/App.tsx`:

```tsx
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { ThemeProvider } from './theme/ThemeContext';
import ThemeToggle from './theme/ThemeToggle';
import SearchPage from './pages/SearchPage';
import AssetPage from './pages/AssetPage';
import styles from './App.module.css';

function NavBar() {
  return (
    <nav className={styles.nav}>
      <Link to="/" className={styles.logo}>
        <span className={styles.logoAccent}>◆</span> Asset Analytics
      </Link>
      <div className={styles.navRight}>
        <Link to="/" style={{ fontSize: 13, color: 'var(--text-muted)' }}>Search</Link>
        <ThemeToggle />
      </div>
    </nav>
  );
}

function PageWrapper({ children }: { children: React.ReactNode }) {
  return <div className={styles.pageFade}>{children}</div>;
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <div className={styles.app}>
          <NavBar />
          <Routes>
            <Route path="/" element={<PageWrapper><SearchPage /></PageWrapper>} />
            <Route path="/asset/:symbol" element={<PageWrapper><AssetPage /></PageWrapper>} />
          </Routes>
        </div>
      </BrowserRouter>
    </ThemeProvider>
  );
}
```

- [ ] **Step 3: Update main.tsx to import global styles**

Rewrite `frontend/src/main.tsx`:

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/tokens.css'
import './styles/global.css'
import './styles/theme.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

- [ ] **Step 4: Verify the app compiles**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx frontend/src/App.module.css frontend/src/main.tsx
git commit -m "feat: add app shell with sticky nav bar and theme toggle"
```

---

### Task 4: Skeleton Component

**Files:**
- Create: `frontend/src/components/Skeleton.tsx`
- Create: `frontend/src/components/Skeleton.module.css`

- [ ] **Step 1: Write Skeleton.module.css**

Create `frontend/src/components/Skeleton.module.css`:

```css
.skeleton {
  background: var(--border-default);
  border-radius: var(--radius-sm);
  animation: shimmer 1.5s infinite;
  background-image: linear-gradient(
    90deg,
    transparent 0,
    rgba(255, 255, 255, 0.06) 50%,
    transparent 100%
  );
  background-size: 200% 100%;
}

[data-theme='dark'] .skeleton {
  background-image: linear-gradient(
    90deg,
    transparent 0,
    rgba(255, 255, 255, 0.03) 50%,
    transparent 100%
  );
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

- [ ] **Step 2: Write Skeleton.tsx**

Create `frontend/src/components/Skeleton.tsx`:

```tsx
import styles from './Skeleton.module.css';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string | number;
  style?: React.CSSProperties;
}

export default function Skeleton({ width, height, borderRadius, style }: SkeletonProps) {
  return (
    <div
      className={styles.skeleton}
      style={{
        width: width ?? '100%',
        height: height ?? 16,
        borderRadius: borderRadius ?? undefined,
        ...style,
      }}
    />
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/Skeleton.tsx frontend/src/components/Skeleton.module.css
git commit -m "feat: add Skeleton component with shimmer animation"
```

---

### Task 5: SearchBar Restyle

**Files:**
- Create: `frontend/src/components/SearchBar.module.css`
- Modify: `frontend/src/components/SearchBar.tsx`

- [ ] **Step 1: Write SearchBar.module.css**

Create `frontend/src/components/SearchBar.module.css`:

```css
.wrapper {
  position: relative;
  max-width: 560px;
  margin: 0 auto;
}

.input {
  width: 100%;
  padding: 12px 16px;
  font-size: 16px;
  font-family: var(--font-sans);
  color: var(--text-primary);
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  outline: none;
  box-sizing: border-box;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.input::placeholder {
  color: var(--text-muted);
}

.input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-subtle);
}

.searching {
  padding: 8px 16px;
  font-size: 13px;
  color: var(--text-muted);
}

.dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  margin: 4px 0 0;
  padding: 0;
  list-style: none;
  z-index: 50;
  box-shadow: var(--shadow-md);
  max-height: 360px;
  overflow-y: auto;
  animation: dropdownIn 0.15s ease;
}

@keyframes dropdownIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

.result {
  padding: 10px 16px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-subtle);
  transition: background var(--transition-fast);
}

.result:last-child {
  border-bottom: none;
}

.result:hover {
  background: var(--accent-subtle);
}

.symbol {
  font-weight: 600;
  font-size: 14px;
  font-family: var(--font-mono);
}

.name {
  font-size: 12px;
  color: var(--text-muted);
}

.meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
}

.tag {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.tagEtf {
  background: rgba(16, 185, 129, 0.1);
  color: var(--green);
}

.tagStock {
  background: var(--accent-subtle);
  color: var(--accent);
}
```

- [ ] **Step 2: Update SearchBar.tsx to use CSS modules**

Rewrite `frontend/src/components/SearchBar.tsx`:

```tsx
import { useState, useEffect, useRef } from 'react';
import { searchAssets } from '../api/client';
import type { AssetSearchResult } from '../api/types';
import styles from './SearchBar.module.css';

export default function SearchBar({ onSelect }: { onSelect: (r: AssetSearchResult) => void }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<AssetSearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (query.length < 1) {
      setResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await searchAssets(query);
        setResults(data);
        setOpen(data.length > 0);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  return (
    <div ref={ref} className={styles.wrapper}>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => results.length > 0 && setOpen(true)}
        placeholder="Search ticker or name (e.g. AAPL, 0700.HK, 300502.SZ)..."
        className={styles.input}
      />
      {loading && <div className={styles.searching}>Searching...</div>}
      {open && results.length > 0 && (
        <ul className={styles.dropdown}>
          {results.map((r) => (
            <li
              key={r.symbol}
              onClick={() => {
                onSelect(r);
                setQuery(r.symbol);
                setOpen(false);
              }}
              className={styles.result}
            >
              <div>
                <div className={styles.symbol}>{r.symbol}</div>
                <div className={styles.name}>{r.name}</div>
              </div>
              <div className={styles.meta}>
                <span className={`${styles.tag} ${r.type === 'etf' ? styles.tagEtf : styles.tagStock}`}>
                  {r.type.toUpperCase()}
                </span>
                <span>{r.exchange}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/SearchBar.tsx frontend/src/components/SearchBar.module.css
git commit -m "feat: restyle SearchBar with CSS modules and animation"
```

---

### Task 6: SearchPage Restyle

**Files:**
- Create: `frontend/src/pages/SearchPage.module.css`
- Modify: `frontend/src/pages/SearchPage.tsx`

- [ ] **Step 1: Write SearchPage.module.css**

Create `frontend/src/pages/SearchPage.module.css`:

```css
.page {
  max-width: 600px;
  margin: 80px auto 0;
  padding: 0 var(--space-5);
  text-align: center;
}

.heroTitle {
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.5px;
  margin-bottom: var(--space-2);
  color: var(--text-primary);
}

.heroSub {
  color: var(--text-muted);
  margin-bottom: var(--space-8);
  font-size: 16px;
  line-height: 1.5;
}

.chips {
  display: flex;
  gap: var(--space-2);
  justify-content: center;
  flex-wrap: wrap;
  margin-top: var(--space-8);
}

.chip {
  padding: 6px 14px;
  font-size: 13px;
  font-family: var(--font-mono);
  font-weight: 500;
  color: var(--text-secondary);
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 20px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.chip:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-subtle);
}
```

- [ ] **Step 2: Update SearchPage.tsx**

Rewrite `frontend/src/pages/SearchPage.tsx`:

```tsx
import { useNavigate } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import type { AssetSearchResult } from '../api/types';
import styles from './SearchPage.module.css';

const POPULAR = ['AAPL', 'MSFT', '0700.HK', '300502.SZ', '7203.T', '^GSPC'];

export default function SearchPage() {
  const navigate = useNavigate();

  function handleSelect(result: AssetSearchResult) {
    navigate(`/asset/${encodeURIComponent(result.symbol)}`);
  }

  function handleChip(symbol: string) {
    navigate(`/asset/${encodeURIComponent(symbol)}`);
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.heroTitle}>Analyze Any Asset, Globally</h1>
      <p className={styles.heroSub}>
        Real-time data · AI-powered insights
      </p>
      <SearchBar onSelect={handleSelect} />
      <div className={styles.chips}>
        {POPULAR.map((s) => (
          <button key={s} className={styles.chip} onClick={() => handleChip(s)}>
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/SearchPage.tsx frontend/src/pages/SearchPage.module.css
git commit -m "feat: restyle SearchPage with hero layout and quick-access chips"
```

---

### Task 7: AssetDetail Restyle

**Files:**
- Create: `frontend/src/components/AssetDetail.module.css`
- Modify: `frontend/src/components/AssetDetail.tsx`

- [ ] **Step 1: Write AssetDetail.module.css**

Create `frontend/src/components/AssetDetail.module.css`:

```css
.card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  margin-bottom: var(--space-6);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.title {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.3px;
  color: var(--text-primary);
}

.subtitle {
  color: var(--text-muted);
  font-size: 14px;
  margin-top: 2px;
  font-family: var(--font-mono);
}

.price {
  text-align: right;
}

.priceValue {
  font-size: 28px;
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--text-primary);
}

.priceCurrency {
  font-size: 14px;
  color: var(--text-muted);
}

.changeUp {
  color: var(--green);
  font-size: 14px;
  font-weight: 500;
}

.changeDown {
  color: var(--red);
  font-size: 14px;
  font-weight: 500;
}

.description {
  color: var(--text-secondary);
  line-height: 1.6;
  font-size: 14px;
  margin-bottom: var(--space-5);
}

.metricsGrid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: var(--space-3);
}

.metric {
  background: var(--bg-primary);
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
}

.metric:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-xs);
}

.metricLabel {
  font-size: 12px;
  color: var(--text-muted);
}

.metricValue {
  font-size: 15px;
  font-weight: 600;
  margin-top: 2px;
  font-family: var(--font-mono);
  color: var(--text-primary);
}
```

- [ ] **Step 2: Update AssetDetail.tsx**

Rewrite `frontend/src/components/AssetDetail.tsx`:

```tsx
import type { AssetDetail as AssetDetailType } from '../api/types';
import styles from './AssetDetail.module.css';

function fmt(n?: number): string {
  if (n == null) return '—';
  if (Math.abs(n) >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  return `$${n.toLocaleString()}`;
}

export default function AssetDetail({ asset }: { asset: AssetDetailType }) {
  const { profile, price, metrics } = asset;
  const isPositive = (price.change ?? 0) >= 0;

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>{profile.name}</h1>
          <div className={styles.subtitle}>
            {asset.symbol} · {profile.sector || '—'} · {profile.country || '—'}
          </div>
        </div>
        <div className={styles.price}>
          <div className={styles.priceValue}>
            {price.current.toLocaleString()}{' '}
            <span className={styles.priceCurrency}>{price.currency}</span>
          </div>
          {price.change != null && (
            <div className={isPositive ? styles.changeUp : styles.changeDown}>
              {isPositive ? '+' : ''}{price.change.toFixed(2)} ({isPositive ? '+' : ''}{price.change_pct?.toFixed(2)}%)
            </div>
          )}
        </div>
      </div>

      {profile.description && (
        <p className={styles.description}>{profile.description}</p>
      )}

      <div className={styles.metricsGrid}>
        <Metric label="Market Cap" value={fmt(profile.market_cap)} />
        <Metric label="P/E Ratio" value={metrics.pe_ratio?.toFixed(2)} />
        <Metric label="P/B Ratio" value={metrics.pb_ratio?.toFixed(2)} />
        <Metric label="EPS" value={metrics.eps != null ? `$${metrics.eps.toFixed(2)}` : undefined} />
        <Metric label="Dividend Yield" value={metrics.dividend_yield != null ? `${(metrics.dividend_yield * 100).toFixed(2)}%` : undefined} />
        <Metric label="Beta" value={metrics.beta?.toFixed(2)} />
        <Metric label="52W High" value={metrics.fifty_two_week_high?.toFixed(2)} />
        <Metric label="52W Low" value={metrics.fifty_two_week_low?.toFixed(2)} />
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value?: string }) {
  return (
    <div className={styles.metric}>
      <div className={styles.metricLabel}>{label}</div>
      <div className={styles.metricValue}>{value || '—'}</div>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/AssetDetail.tsx frontend/src/components/AssetDetail.module.css
git commit -m "feat: restyle AssetDetail as surface card with hover metrics"
```

---

### Task 8: PriceChart Restyle

**Files:**
- Create: `frontend/src/components/PriceChart.module.css`
- Modify: `frontend/src/components/PriceChart.tsx`

- [ ] **Step 1: Write PriceChart.module.css**

Create `frontend/src/components/PriceChart.module.css`:

```css
.card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  margin-bottom: var(--space-6);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
}

.sectionTitle {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.periods {
  display: flex;
  gap: 4px;
}

.periodBtn {
  padding: 4px 12px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--bg-surface);
  color: var(--text-muted);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  font-family: var(--font-sans);
  transition: all var(--transition-fast);
}

.periodBtn:hover {
  border-color: var(--text-muted);
  color: var(--text-primary);
}

.periodBtnActive {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}

.empty {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 14px;
}
```

- [ ] **Step 2: Update PriceChart.tsx**

Rewrite `frontend/src/components/PriceChart.tsx`:

```tsx
import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { getPriceHistory } from '../api/client';
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
        <h3 className={styles.sectionTitle}>Price History</h3>
        <div className={styles.periods}>
          {PERIODS.map((p) => (
            <button
              key={p.value}
              onClick={() => setPeriod(p.value)}
              className={`${styles.periodBtn} ${period === p.value ? styles.periodBtnActive : ''}`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>
      {loading ? (
        <div className={styles.empty}>Loading chart...</div>
      ) : chartData.length === 0 ? (
        <div className={styles.empty}>No price data available for this period</div>
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
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/PriceChart.tsx frontend/src/components/PriceChart.module.css
git commit -m "feat: restyle PriceChart as surface card with themed chart"
```

---

### Task 9: NewsList Restyle

**Files:**
- Create: `frontend/src/components/NewsList.module.css`
- Modify: `frontend/src/components/NewsList.tsx`

- [ ] **Step 1: Write NewsList.module.css**

Create `frontend/src/components/NewsList.module.css`:

```css
.card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  margin-bottom: var(--space-6);
}

.sectionTitle {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: var(--space-4);
  color: var(--text-primary);
}

.list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.article {
  text-decoration: none;
  color: inherit;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  display: block;
  transition: border-color var(--transition-fast);
}

.article:hover {
  border-color: var(--accent);
}

.articleTitle {
  font-weight: 500;
  font-size: 14px;
  margin-bottom: 3px;
  color: var(--text-primary);
}

.articleMeta {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: var(--text-muted);
}
```

- [ ] **Step 2: Update NewsList.tsx**

Rewrite `frontend/src/components/NewsList.tsx`:

```tsx
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
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/NewsList.tsx frontend/src/components/NewsList.module.css
git commit -m "feat: restyle NewsList as surface card with accent hover"
```

---

### Task 10: SettingsDialog Restyle

**Files:**
- Create: `frontend/src/components/SettingsDialog.module.css`
- Modify: `frontend/src/components/SettingsDialog.tsx`

- [ ] **Step 1: Write SettingsDialog.module.css**

Create `frontend/src/components/SettingsDialog.module.css`:

```css
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  animation: overlayIn 0.15s ease;
}

@keyframes overlayIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  padding: 28px;
  max-width: 420px;
  width: 90%;
  box-shadow: var(--shadow-lg);
  animation: modalIn 0.2s ease;
}

@keyframes modalIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

.title {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 var(--space-5);
  color: var(--text-primary);
}

.label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 4px;
  margin-top: var(--space-3);
  color: var(--text-secondary);
}

.input {
  width: 100%;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-default);
  font-size: 14px;
  font-family: var(--font-sans);
  box-sizing: border-box;
  outline: none;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: border-color var(--transition-fast);
}

.input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-subtle);
}

.select {
  composes: input;
  cursor: pointer;
}

.actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: var(--space-5);
}

.btnCancel {
  padding: 8px 20px;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  font-family: var(--font-sans);
  background: var(--border-default);
  color: var(--text-secondary);
}

.btnSave {
  padding: 8px 20px;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  font-family: var(--font-sans);
  background: var(--accent);
  color: white;
}

.btnSave:disabled {
  background: var(--border-default);
  color: var(--text-muted);
  cursor: not-allowed;
}
```

- [ ] **Step 2: Update SettingsDialog.tsx**

Rewrite `frontend/src/components/SettingsDialog.tsx` (logic unchanged, styles only):

```tsx
import { useState } from 'react';
import type { AnalysisRequest } from '../api/types';
import styles from './SettingsDialog.module.css';

const STORAGE_KEY = 'llm_settings';

export function loadSettings(): AnalysisRequest | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

function saveSettings(settings: AnalysisRequest) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: (s: AnalysisRequest) => void;
}

const PROVIDERS = [
  { value: 'claude', label: 'Claude (Anthropic)' },
  { value: 'openai', label: 'GPT (OpenAI)' },
  { value: 'deepseek', label: 'DeepSeek' },
];

export default function SettingsDialog({ open, onClose, onSaved }: Props) {
  const existing = loadSettings();
  const [provider, setProvider] = useState(existing?.provider || 'claude');
  const [model, setModel] = useState(existing?.model || '');
  const [apiKey, setApiKey] = useState(existing?.api_key || '');
  const [baseUrl, setBaseUrl] = useState(existing?.base_url || '');

  if (!open) return null;

  function handleSave() {
    const settings: AnalysisRequest = { provider, model, api_key: apiKey, base_url: baseUrl || undefined };
    saveSettings(settings);
    onSaved(settings);
    onClose();
  }

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <h3 className={styles.title}>LLM Settings</h3>

        <label className={styles.label}>Provider</label>
        <select value={provider} onChange={(e) => setProvider(e.target.value)} className={styles.select}>
          {PROVIDERS.map((p) => (
            <option key={p.value} value={p.value}>{p.label}</option>
          ))}
        </select>

        <label className={styles.label}>Model Name</label>
        <input
          type="text" value={model} onChange={(e) => setModel(e.target.value)}
          placeholder={provider === 'claude' ? 'claude-sonnet-4-6' : provider === 'openai' ? 'gpt-4o' : 'deepseek-chat'}
          className={styles.input}
        />

        <label className={styles.label}>API Key</label>
        <input
          type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)}
          placeholder="sk-..."
          className={styles.input}
        />

        <label className={styles.label}>Base URL (optional)</label>
        <input
          type="text" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)}
          placeholder={provider === 'deepseek' ? 'https://api.deepseek.com/v1' : 'Leave empty for default'}
          className={styles.input}
        />

        <div className={styles.actions}>
          <button onClick={onClose} className={styles.btnCancel}>Cancel</button>
          <button
            onClick={handleSave}
            disabled={!model || !apiKey}
            className={styles.btnSave}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/SettingsDialog.tsx frontend/src/components/SettingsDialog.module.css
git commit -m "feat: restyle SettingsDialog with modal animation and themed inputs"
```

---

### Task 11: AnalyzePanel Restyle

**Files:**
- Create: `frontend/src/components/AnalyzePanel.module.css`
- Modify: `frontend/src/components/AnalyzePanel.tsx`

- [ ] **Step 1: Write AnalyzePanel.module.css**

Create `frontend/src/components/AnalyzePanel.module.css`:

```css
.panel {
  margin-bottom: var(--space-6);
}

.actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.btnAnalyze {
  padding: 10px 24px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 15px;
  font-weight: 600;
  font-family: var(--font-sans);
  cursor: pointer;
  transition: box-shadow var(--transition-fast);
}

.btnAnalyze:hover:not(:disabled) {
  box-shadow: 0 0 16px rgba(109, 93, 252, 0.35);
}

.btnAnalyze:disabled {
  background: var(--border-default);
  color: var(--text-muted);
  cursor: not-allowed;
}

.btnSettings {
  padding: 10px 16px;
  background: transparent;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  font-size: 13px;
  font-family: var(--font-sans);
  cursor: pointer;
  color: var(--text-muted);
  transition: all var(--transition-fast);
}

.btnSettings:hover {
  border-color: var(--text-muted);
  color: var(--text-primary);
}

.error {
  padding: 12px;
  background: var(--red-subtle);
  color: var(--red);
  border-radius: var(--radius-sm);
  font-size: 14px;
  margin-bottom: var(--space-3);
}

.result {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
}

.resultMeta {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: var(--space-4);
}

.resultContent {
  line-height: 1.7;
  font-size: 14px;
  color: var(--text-primary);
}

.resultContent h2 {
  font-size: 18px;
  margin: var(--space-6) 0 var(--space-2);
}

.resultContent h3 {
  font-size: 15px;
  margin: var(--space-4) 0 var(--space-1);
}

.resultContent p {
  margin: var(--space-2) 0;
}

.resultContent ul,
.resultContent ol {
  padding-left: var(--space-5);
}

.resultContent li {
  margin-bottom: var(--space-1);
}

.resultContent strong {
  font-weight: 600;
}
```

- [ ] **Step 2: Update AnalyzePanel.tsx**

Rewrite `frontend/src/components/AnalyzePanel.tsx`:

```tsx
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { analyzeAsset } from '../api/client';
import { loadSettings } from './SettingsDialog';
import type { AnalysisResponse } from '../api/types';
import styles from './AnalyzePanel.module.css';

interface Props {
  symbol: string;
  onOpenSettings: () => void;
}

export default function AnalyzePanel({ symbol, onOpenSettings }: Props) {
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAnalyze() {
    const settings = loadSettings();
    if (!settings) {
      onOpenSettings();
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await analyzeAsset(symbol, settings);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.panel}>
      <div className={styles.actions}>
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className={styles.btnAnalyze}
        >
          {loading ? 'Analyzing...' : 'Analyze with AI'}
        </button>
        <button onClick={onOpenSettings} className={styles.btnSettings}>
          LLM Settings
        </button>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {result && (
        <div className={styles.result}>
          <div className={styles.resultMeta}>
            Analysis by {result.model_used} · {result.context_sent.news_count} news articles
          </div>
          <div className={styles.resultContent}>
            <ReactMarkdown>{result.analysis}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/AnalyzePanel.tsx frontend/src/components/AnalyzePanel.module.css
git commit -m "feat: restyle AnalyzePanel with glow hover and markdown styling"
```

---

### Task 12: AssetPage Restyle with Skeletons

**Files:**
- Create: `frontend/src/pages/AssetPage.module.css`
- Modify: `frontend/src/pages/AssetPage.tsx`

- [ ] **Step 1: Write AssetPage.module.css**

Create `frontend/src/pages/AssetPage.module.css`:

```css
.page {
  max-width: 860px;
  margin: 0 auto;
  padding: var(--space-6) var(--space-5) 60px;
}

.backLink {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: var(--space-5);
  transition: color var(--transition-fast);
}

.backLink:hover {
  color: var(--text-primary);
}

.skeleton {
  max-width: 860px;
  margin: 0 auto;
  padding: var(--space-6) var(--space-5);
}
```

- [ ] **Step 2: Update AssetPage.tsx with skeletons and back link**

Rewrite `frontend/src/pages/AssetPage.tsx`:

```tsx
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
        <Link to="/" className={styles.backLink}>← Back to search</Link>
        <div style={{ padding: 24, background: 'var(--red-subtle)', color: 'var(--red)', borderRadius: 'var(--radius-md)', fontSize: 14 }}>
          Error: {error}
        </div>
      </div>
    );
  }

  if (!asset) return null;

  return (
    <div className={styles.page}>
      <Link to="/" className={styles.backLink}>← Back to search</Link>
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
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/AssetPage.tsx frontend/src/pages/AssetPage.module.css
git commit -m "feat: add skeleton loading states and back navigation to AssetPage"
```

---

### Task 13: Final Verification

**Files:**
- None created or modified

- [ ] **Step 1: Type-check the entire frontend**

```bash
cd frontend && npx tsc --noEmit
```
Expected: No errors.

- [ ] **Step 2: Build the frontend**

```bash
cd frontend && npm run build
```
Expected: Build succeeds with no errors.

- [ ] **Step 3: Verify all CSS modules are accounted for**

```bash
ls frontend/src/components/*.module.css frontend/src/pages/*.module.css frontend/src/*.module.css
```
Expected: All 8 module.css files exist (SearchBar, AssetDetail, PriceChart, NewsList, SettingsDialog, AnalyzePanel, SearchPage, AssetPage, App).

- [ ] **Step 4: Confirm no inline style objects remain (spot check)**

```bash
grep -r "style={{" frontend/src/ --include="*.tsx" | grep -v node_modules
```
Expected: Only allowed inline styles remain (Skeleton dynamic styles, ThemeToggle, Tooltip contentStyle). No component layout/styles done via inline objects.

- [ ] **Step 5: Commit verification results**

```bash
git add -A && git diff --cached --stat
```
If any fixups were needed, commit them. Otherwise note "Verification passed."
```

