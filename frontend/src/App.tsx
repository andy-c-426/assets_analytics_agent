import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { ThemeProvider } from './theme/ThemeContext';
import ThemeToggle from './theme/ThemeToggle';
import { LocaleProvider, useLocale } from './i18n/LocaleContext';
import LanguageToggle from './components/LanguageToggle';
import SearchPage from './pages/SearchPage';
import AssetPage from './pages/AssetPage';
import styles from './App.module.css';

function NavBar() {
  const { t } = useLocale();
  return (
    <nav className={styles.nav}>
      <Link to="/" className={styles.logo}>
        <span className={styles.logoAccent}>◆</span> {t('nav.brand')}
      </Link>
      <div className={styles.navRight}>
        <Link to="/" className={styles.navLink}>{t('nav.search')}</Link>
        <LanguageToggle className={styles.themeToggle} />
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
      <LocaleProvider>
        <BrowserRouter>
          <div className={styles.app}>
            <NavBar />
            <Routes>
              <Route path="/" element={<PageWrapper><SearchPage /></PageWrapper>} />
              <Route path="/asset/:symbol" element={<PageWrapper><AssetPage /></PageWrapper>} />
            </Routes>
          </div>
        </BrowserRouter>
      </LocaleProvider>
    </ThemeProvider>
  );
}
