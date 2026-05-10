import { useLocale } from '../i18n/LocaleContext';

export default function LanguageToggle({ className }: { className?: string }) {
  const { locale, setLocale } = useLocale();

  function toggle() {
    setLocale(locale === 'en' ? 'zh-CN' : 'en');
  }

  return (
    <button
      onClick={toggle}
      aria-label={`Switch language to ${locale === 'en' ? '简体中文' : 'English'}`}
      className={className}
    >
      {locale === 'en' ? '中' : 'EN'}
    </button>
  );
}
