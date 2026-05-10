type Lang = 'en' | 'zh-CN';

const translations: Record<string, Record<Lang, string>> = {
  'app.title': { en: 'Asset Analytics', 'zh-CN': '资产分析' },
  'nav.brand': { en: 'Asset Analytics', 'zh-CN': '资产分析' },
  'nav.search': { en: 'Search', 'zh-CN': '搜索' },

  'home.title': { en: 'Analyze Any Asset, Globally', 'zh-CN': '全球资产智能分析' },
  'home.subtitle': { en: 'Real-time data · AI-powered insights', 'zh-CN': '实时数据 · AI 驱动洞察' },

  'search.placeholder': { en: 'Search ticker or name (e.g. AAPL, 0700.HK, 300502.SZ)...', 'zh-CN': '搜索代码或名称（如 AAPL、0700.HK、300502.SZ）...' },
  'search.searching': { en: 'Searching...', 'zh-CN': '搜索中...' },

  'detail.showMore': { en: 'Show more', 'zh-CN': '展开更多' },
  'detail.showLess': { en: 'Show less', 'zh-CN': '收起' },
  'detail.marketCap': { en: 'Market Cap', 'zh-CN': '总市值' },
  'detail.peRatio': { en: 'P/E Ratio', 'zh-CN': '市盈率' },
  'detail.pbRatio': { en: 'P/B Ratio', 'zh-CN': '市净率' },
  'detail.eps': { en: 'EPS', 'zh-CN': '每股收益' },
  'detail.dividendYield': { en: 'Dividend Yield', 'zh-CN': '股息率' },
  'detail.beta': { en: 'Beta', 'zh-CN': '贝塔系数' },
  'detail.52wHigh': { en: '52W High', 'zh-CN': '52周最高' },
  'detail.52wLow': { en: '52W Low', 'zh-CN': '52周最低' },

  'chart.title': { en: 'Price History', 'zh-CN': '价格走势' },
  'chart.1M': { en: '1M', 'zh-CN': '1月' },
  'chart.6M': { en: '6M', 'zh-CN': '6月' },
  'chart.1Y': { en: '1Y', 'zh-CN': '1年' },
  'chart.5Y': { en: '5Y', 'zh-CN': '5年' },
  'chart.Max': { en: 'Max', 'zh-CN': '全部' },
  'chart.loading': { en: 'Loading chart...', 'zh-CN': '加载图表...' },
  'chart.noData': { en: 'No price data available for this period', 'zh-CN': '该时间段无价格数据' },

  'news.title': { en: 'Recent News', 'zh-CN': '最新资讯' },

  'analyze.button': { en: 'Analyze with AI', 'zh-CN': 'AI 智能分析' },
  'analyze.analyzing': { en: 'Analyzing...', 'zh-CN': '分析中...' },
  'analyze.settings': { en: 'LLM Settings', 'zh-CN': 'LLM 设置' },
  'analyze.planning': { en: 'Planning analysis...', 'zh-CN': '正在规划分析...' },
  'analyze.evaluating': { en: 'Evaluating results...', 'zh-CN': '正在评估结果...' },
  'analyze.synthesizing': { en: 'Writing analysis report...', 'zh-CN': '正在撰写分析报告...' },
  'analyze.fetchingData': { en: 'Fetching data: {tool}', 'zh-CN': '获取数据: {tool}' },
  'analyze.failed': { en: 'Analysis failed', 'zh-CN': '分析失败' },

  'settings.title': { en: 'LLM Settings', 'zh-CN': 'LLM 设置' },
  'settings.provider': { en: 'Provider', 'zh-CN': '服务商' },
  'settings.model': { en: 'Model Name', 'zh-CN': '模型名称' },
  'settings.apiKey': { en: 'API Key', 'zh-CN': 'API 密钥' },
  'settings.baseUrl': { en: 'Base URL (optional)', 'zh-CN': '接口地址（可选）' },
  'settings.baseUrlPlaceholder': { en: 'Leave empty for default', 'zh-CN': '留空使用默认地址' },
  'settings.finnhubKey': { en: 'Finnhub API Key (optional — for news)', 'zh-CN': 'Finnhub API 密钥（可选 — 用于新闻）' },
  'settings.finnhubPlaceholder': { en: 'Free key from https://finnhub.io/register', 'zh-CN': '从 https://finnhub.io/register 免费获取' },
  'settings.cancel': { en: 'Cancel', 'zh-CN': '取消' },
  'settings.save': { en: 'Save', 'zh-CN': '保存' },
  'settings.language': { en: 'Language', 'zh-CN': '语言' },

  'asset.back': { en: '← Back to search', 'zh-CN': '← 返回搜索' },
  'asset.error': { en: 'Error: {message}', 'zh-CN': '错误: {message}' },

  'lang.en': { en: 'English', 'zh-CN': 'English' },
  'lang.zh-CN': { en: '简体中文', 'zh-CN': '简体中文' },
};

export type Locale = Lang;

export function t(locale: Locale, key: string, vars?: Record<string, string>): string {
  const entry = translations[key];
  let text: string;
  if (entry && entry[locale]) {
    text = entry[locale];
  } else if (entry && entry['en']) {
    text = entry['en'];
  } else {
    text = key;
  }
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      text = text.replace(`{${k}}`, v);
    }
  }
  return text;
}
