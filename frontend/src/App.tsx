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
        <ThemeToggle className={styles.themeToggle} />
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
