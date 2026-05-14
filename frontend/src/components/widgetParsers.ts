/* ------------------------------------------------------------------ */
/*  Parsers — extract structured data from raw tool output            */
/* ------------------------------------------------------------------ */

export interface MarketData {
  source: 'futu' | 'yfinance' | 'unknown';
  name: string;
  symbol: string;
  asOf: string;
  currency: string;
  price: {
    current: string;
    change: string;
    changePct: string;
    open: string;
    high: string;
    low: string;
    prevClose: string;
  };
  volume: { label: string; value: string }[];
  valuation: { label: string; value: string }[];
  fundamentals: { label: string; value: string }[];
  week52: { high: string; low: string } | null;
  stockInfo: { label: string; value: string }[];
}

export interface MacroResearch {
  region: string;
  index: string;
  currency: string;
  note: string;
  newsItems: { date: string; title: string; body: string; source: string }[];
  sector: string;
  industry: string;
  sectorEtf: { symbol: string; price: string } | null;
}

export interface SentimentNews {
  source: string;
  period: string;
  articleCount: number;
  categories: {
    name: string;
    count: number;
    articles: {
      date: string;
      headline: string;
      source: string;
      url: string;
      summary: string;
    }[];
  }[];
}

export interface CapitalFlowData {
  source: 'akshare';
  symbol: string;
  flowItems: {
    board: string;
    direction: string;
    netBuy: string;
    netFlow: string;
    advancesDeclines: string;
    indexName: string;
    indexChange: string;
  }[];
  holdings: {
    date: string;
    close: string;
    change: string;
    shares: string;
    value: string;
    pct: string;
    chg1d: string;
    chg5d: string;
  } | null;
}

export interface CnMarketSentiment {
  source: 'akshare';
  symbol: string;
  sectors: {
    name: string;
    netFlow: string;
    pct: string;
    type: 'inflow' | 'outflow';
  }[];
  lhb: {
    appearances: number;
    cumulativeBuy: string;
    cumulativeSell: string;
    recent: { date: string; close: string; reason: string }[];
  } | null;
  topStocks: {
    code: string;
    name: string;
    price: string;
    change: string;
    netFlow: string;
    pct: string;
  }[];
}

export interface UsFundamentals {
  source: 'yfinance';
  symbol: string;
  analystTargets: {
    current: string;
    low: string;
    mean: string;
    median: string;
    high: string;
    premium: string;
  } | null;
  recommendations: { label: string; count: number }[];
  insiderTrades: {
    date: string;
    name: string;
    transaction: string;
    shares: string;
    value: string;
  }[];
  institutionalHolders: {
    holder: string;
    shares: string;
    pct: string;
  }[];
  ownershipSummary: { label: string; value: string }[];
  earnings: {
    date: string;
    type: 'upcoming' | 'past';
    epsEstimate: string;
    epsActual: string;
    surprise: string;
  }[];
  secFilings: {
    date: string;
    type: string;
    title: string;
    url: string;
  }[];
}

/* ------------------------------------------------------------------ */
/*  Market Data Parser                                                */
/* ------------------------------------------------------------------ */

export function parseMarketData(raw: string): MarketData | null {
  const lines = raw.split('\n');
  const result: MarketData = {
    source: 'unknown',
    name: '',
    symbol: '',
    asOf: '',
    currency: '$',
    price: { current: '', change: '', changePct: '', open: '', high: '', low: '', prevClose: '' },
    volume: [],
    valuation: [],
    fundamentals: [],
    week52: null,
    stockInfo: [],
  };

  if (raw.includes('Futu Real-Time Data')) result.source = 'futu';
  else if (raw.includes('yfinance Market Data')) result.source = 'yfinance';

  const hdrMatch = raw.match(/=== (?:Futu Real-Time Data|yfinance Market Data):\s*(.+?)\s*\(([^)]+)\)\s*===/);
  if (hdrMatch) {
    result.name = hdrMatch[1].trim();
    result.symbol = hdrMatch[2].trim();
    // Derive currency from Futu code prefix (e.g. HK.00700 → HKD)
    const codePrefix = result.symbol.split('.')[0];
    const futuCurrencyMap: Record<string, string> = {
      US: '$', HK: 'HK$', SH: '¥', SZ: '¥',
      JP: '¥', KR: '₩', TW: 'NT$', SG: 'S$',
      AU: 'A$', CA: 'C$', UK: '£',
    };
    if (futuCurrencyMap[codePrefix]) {
      result.currency = futuCurrencyMap[codePrefix];
    }
  }

  // Currency from yfinance line: "Current Price: 123.45 USD"
  const currencyMatch = raw.match(/Current Price:\s*[\d.]+\s*(\w+)/);
  if (currencyMatch && result.source === 'yfinance') {
    const iso = currencyMatch[1];
    const isoMap: Record<string, string> = {
      USD: '$', HKD: 'HK$', CNY: '¥', JPY: '¥',
      KRW: '₩', TWD: 'NT$', SGD: 'S$', AUD: 'A$',
      CAD: 'C$', GBP: '£', EUR: '€', CHF: 'CHF',
    };
    result.currency = isoMap[iso] || iso;
  }

  const asOfMatch = raw.match(/As of:\s*(.+)/);
  if (asOfMatch) result.asOf = asOfMatch[1].trim();

  let section = '';
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    if (line === '[Price]') { section = 'price'; continue; }
    if (line === '[Volume]') { section = 'volume'; continue; }
    if (line === '[Valuation]') { section = 'valuation'; continue; }
    if (line === '[Fundamentals]') { section = 'fundamentals'; continue; }
    if (line === '[Key Metrics]') { section = 'valuation'; continue; }
    if (line === '[52-Week Range]') { section = 'week52'; continue; }

    if (line.startsWith('=== Stock Info:')) {
      section = 'stockInfo';
      continue;
    }

    if (!line || line.startsWith('===')) continue;

    if (section === 'price') {
      if (line.startsWith('Current:')) {
        const parts = line.replace('Current:', '').trim();
        const changeM = parts.match(/Change:\s*([+-][\d.]+)\s*\(([+-][\d.]+)%\)/);
        if (changeM) {
          result.price.current = parts.split('Change:')[0].trim();
          result.price.change = changeM[1];
          result.price.changePct = changeM[2];
        } else {
          result.price.current = parts;
        }
      }
      const m = line.match(/^(.+?):\s*(.+)$/);
      if (m) {
        const key = m[1].toLowerCase().replace(/\s+/g, '');
        if (key === 'open') result.price.open = m[2];
        else if (key === 'high') result.price.high = m[2];
        else if (key === 'low') result.price.low = m[2];
        else if (key === 'prevclose') result.price.prevClose = m[2];
      }
    }

    if (line.startsWith('Sector:') && !result.stockInfo.length) {
      const parts = line.split('|').map(s => s.trim());
      for (const p of parts) {
        const m = p.match(/^(.+?):\s*(.+)$/);
        if (m) result.stockInfo.push({ label: m[1], value: m[2] });
      }
    }

    if (line.startsWith('Market Cap:')) {
      result.valuation.push({ label: 'Market Cap', value: line.replace('Market Cap:', '').trim() });
    }
    if (line.startsWith('Current Price:')) {
      result.price.current = line.replace('Current Price:', '').trim();
    }
    if (line.startsWith('Change:') && !result.price.change) {
      const changeM = line.match(/Change:\s*([+-][\d.]+)\s*\(([+-][\d.]+)%\)/);
      if (changeM) {
        result.price.change = changeM[1];
        result.price.changePct = changeM[2];
      }
    }

    if (['volume', 'valuation', 'fundamentals', 'week52'].includes(section)) {
      const m = line.match(/^(.+?):\s*(.+)$/);
      if (m) {
        const kv = { label: m[1].trim(), value: m[2].trim() };
        if (section === 'volume') result.volume.push(kv);
        else if (section === 'valuation') {
          if (kv.label !== 'Market Cap') result.valuation.push(kv);
        } else if (section === 'fundamentals') result.fundamentals.push(kv);
        else if (section === 'week52') {
          if (!result.week52) result.week52 = { high: '', low: '' };
          if (kv.label.toLowerCase().includes('high')) result.week52.high = kv.value;
          else if (kv.label.toLowerCase().includes('low')) result.week52.low = kv.value;
        }
      }
    }

    if (section === 'stockInfo') {
      const m = line.match(/^(.+?):\s*(.+)$/);
      if (m) result.stockInfo.push({ label: m[1], value: m[2] });
    }
  }

  return result.name ? result : null;
}

/* ------------------------------------------------------------------ */
/*  Macro Research Parser                                             */
/* ------------------------------------------------------------------ */

export function parseMacroResearch(raw: string): MacroResearch | null {
  const result: MacroResearch = {
    region: '',
    index: '',
    currency: '$',
    note: '',
    newsItems: [],
    sector: '',
    industry: '',
    sectorEtf: null,
  };

  const hdrMatch = raw.match(/=== Macro & Sector Research\s*\(([^/]+)\s*\/\s*([^)]+)\)\s*===/);
  if (hdrMatch) {
    result.region = hdrMatch[1].trim();
    result.index = hdrMatch[2].trim();
  }

  // Currency from market header: "Market: HKEX | Currency: HKD"
  const curMatch = raw.match(/Currency:\s*(\w+)/);
  if (curMatch) {
    const iso = curMatch[1];
    const isoMap: Record<string, string> = {
      USD: '$', HKD: 'HK$', CNY: '¥', JPY: '¥',
      KRW: '₩', TWD: 'NT$', SGD: 'S$', AUD: 'A$',
      CAD: 'C$', GBP: '£', EUR: '€', CHF: 'CHF',
    };
    result.currency = isoMap[iso] || iso;
  }

  const noteMatch = raw.match(/^\(Note:[^)]+\)/m);
  if (noteMatch) result.note = noteMatch[0];

  // Split by section headers: "--- Ticker: ... ---" or "--- Macro: ... ---"
  const querySections = raw.split(/^--- (?:Ticker|Macro):\s*.*\s*---$/m);
  if (querySections.length > 1) {
    for (let i = 1; i < querySections.length; i++) {
      const lines = querySections[i].split('\n');
      let current: { date: string; title: string; body: string; source: string } | null = null;
      for (const line of lines) {
        const itemMatch = line.match(/^-\s*\[([^\]]+)\]\s*(.+)/);
        if (itemMatch) {
          if (current) result.newsItems.push(current);
          current = { date: itemMatch[1], title: itemMatch[2], body: '', source: '' };
        } else if (current) {
          const bodyMatch = line.match(/^\s+(.+)/);
          const sourceMatch = line.match(/^\s*Source:\s*(.+)/);
          if (sourceMatch) {
            current.source = sourceMatch[1].trim();
          } else if (bodyMatch && !current.body) {
            current.body = bodyMatch[1].trim();
          }
        }
      }
      if (current) result.newsItems.push(current);
    }
  }

  const sectorMatch = raw.match(/Sector:\s*(.+)/);
  if (sectorMatch) result.sector = sectorMatch[1].trim();
  const industryMatch = raw.match(/Industry:\s*(.+)/);
  if (industryMatch) result.industry = industryMatch[1].trim();
  const etfMatch = raw.match(/(\w+)\s*Sector ETF\s*\((\w+)\):\s*\$?([\d.]+)/);
  if (etfMatch) {
    result.sectorEtf = { symbol: etfMatch[2], price: etfMatch[3] };
  }

  return result.region ? result : null;
}

/* ------------------------------------------------------------------ */
/*  Sentiment News Parser                                             */
/* ------------------------------------------------------------------ */

export function parseSentimentNews(raw: string): SentimentNews | null {
  const result: SentimentNews = {
    source: '',
    period: '',
    articleCount: 0,
    categories: [],
  };

  if (raw.includes('Finnhub')) result.source = 'Finnhub';
  else if (raw.includes('yfinance')) result.source = 'yfinance';
  else if (raw.includes('Web Search')) result.source = 'Web Search';

  if (!result.source) return null;

  const hdrMatch = raw.match(/=== Sentiment & News\s*(?:\(([^)]+)\))?[=:]*\s*(.+?)\s*===/);
  if (!hdrMatch && !raw.includes('No web news') && !raw.includes('temporarily unavailable')) {
    return null;
  }

  const periodMatch = raw.match(/Period:\s*(.+)/);
  if (periodMatch) result.period = periodMatch[1];

  const countMatch = raw.match(/(?:Articles|Results):\s*(\d+)/);
  if (countMatch) result.articleCount = parseInt(countMatch[1]);

  // Category sections for Finnhub format: --- CATEGORY (N articles) ---
  const catRegex = /---\s*(.+?)\s*\((\d+)\s*articles?\)\s*---/g;
  const catSections: { start: number; end: number; name: string; count: number }[] = [];
  let catMatch: RegExpExecArray | null;
  while ((catMatch = catRegex.exec(raw)) !== null) {
    catSections.push({
      start: catMatch.index + catMatch[0].length,
      end: Infinity,
      name: catMatch[1].trim(),
      count: parseInt(catMatch[2]),
    });
  }
  for (let i = 0; i < catSections.length; i++) {
    catSections[i].end = i + 1 < catSections.length ? catSections[i + 1].start : raw.length;
  }

  // If no category sections found (yfinance / web search), treat all articles as one "News" category
  if (catSections.length === 0) {
    const lines = raw.split('\n');
    // Count actual article blocks
    const articleHeaders = lines.filter(l => /^\s*-?\s*\[[\d]{4}-[\d]{2}-[\d]{2}[^\]]*\]/.test(l));
    if (articleHeaders.length > 0) {
      catSections.push({ start: 0, end: raw.length, name: 'News', count: articleHeaders.length });
    }
  }

  for (const cs of catSections) {
    const sectionText = raw.slice(cs.start, cs.end);
    const articles: SentimentNews['categories'][0]['articles'] = [];
    // Split by article headers: either "[YYYY-MM-DD" or "- [YYYY-MM-DD"
    const articleBlocks = sectionText.split(/\n(?=\s*-?\s*\[[\d]{4}-)/);
    for (const block of articleBlocks) {
      // Match date+headline: optional "- " then "[date] headline"
      const dateMatch = block.match(/^\s*-?\s*\[([^\]]+)\]\s*(.+)/);
      if (!dateMatch) continue;

      const sourceMatch = block.match(/(?:Source|Publisher):\s*(.+?)\s*\|?\s*(https?:\/\/\S+)?/m);
      const linkMatch = block.match(/Link:\s*(https?:\/\/\S+)/m);
      const summaryMatch = block.match(/(?:Summary|Body):\s*(.+?)(?:\n|$)/m);

      const source = sourceMatch ? sourceMatch[1].trim() : '';
      const url = (sourceMatch && sourceMatch[2]) ? sourceMatch[2].trim() : (linkMatch ? linkMatch[1].trim() : '');

      articles.push({
        date: dateMatch[1].trim(),
        headline: dateMatch[2].trim(),
        source,
        url,
        summary: summaryMatch ? summaryMatch[1].trim() : '',
      });
    }
    if (articles.length) {
      result.categories.push({ name: cs.name, count: cs.count || articles.length, articles });
    }
  }

  return result.categories.length > 0 ? result : null;
}

/* ------------------------------------------------------------------ */
/*  Capital Flow Parser                                                */
/* ------------------------------------------------------------------ */

export function parseCapitalFlow(raw: string): CapitalFlowData | null {
  if (!raw.includes("Stock Connect")) return null;

  const result: CapitalFlowData = {
    source: 'akshare',
    symbol: '',
    flowItems: [],
    holdings: null,
  };

  const hdrMatch = raw.match(/=== Capital Flow & Stock Connect:\s*(.+?)\s*===/);
  if (hdrMatch) result.symbol = hdrMatch[1].trim();

  // Parse flow summary lines: "沪股通 — Northbound (北向), Net Buy: +X.XX 亿元, ..."
  const flowSection = raw.split('--- Stock Connect Holdings:')[0] || raw;
  const flowLines = flowSection.split('\n');
  for (const line of flowLines) {
    // Match a flow entry line: contains "— Northbound" or "— Southbound"
    const boardMatch = line.match(/^(.+?)\s*—\s*(Northbound|Southbound)\s*(?:\([^)]+\))?/);
    if (!boardMatch) continue;

    const board = boardMatch[1].trim();
    const direction = boardMatch[2].trim();

    const netBuyM = line.match(/Net Buy:\s*([+-][\d.]+)\s*亿元/);
    const netFlowM = line.match(/Net Flow:\s*([+-]?[\d.]+)\s*亿元/);
    const advM = line.match(/Advances\/Declines:\s*(\d+)\/(\d+)\s*\((\d+)\s*flat\)/);
    const idxM = line.match(/([^\s,]+(?:指数|成指|Index)):\s*([+-][\d.]+)%/);

    result.flowItems.push({
      board,
      direction,
      netBuy: netBuyM ? `${netBuyM[1]} 亿` : '',
      netFlow: netFlowM ? `${netFlowM[1]} 亿` : '',
      advancesDeclines: advM ? `${advM[1]}/${advM[2]} (${advM[3]} flat)` : '',
      indexName: idxM ? idxM[1] : '',
      indexChange: idxM ? `${idxM[2]}%` : '',
    });
  }

  // Parse holdings section
  const holdingsSection = raw.split('--- Stock Connect Holdings:')[1];
  if (holdingsSection) {
    const hLines = holdingsSection.split('\n');
    const h: CapitalFlowData['holdings'] = {
      date: '', close: '', change: '', shares: '', value: '', pct: '', chg1d: '', chg5d: '',
    };
    const codeMatch = holdingsSection.match(/^([\w.]+)\s*---/m);
    // skip code line

    const dateM = holdingsSection.match(/Latest:\s*(.+)/);
    if (dateM) h.date = dateM[1].trim();

    const closeM = holdingsSection.match(/Close:\s*([\d.]+)\s*\|\s*Change:\s*([+-]?[\d.]+)%/);
    if (closeM) { h.close = closeM[1]; h.change = `${closeM[2]}%`; }

    const sharesM = holdingsSection.match(/Holdings:\s*([\d,]+)\s*shares\s*\|\s*Value:\s*([\d.]+)\s*亿元/);
    if (sharesM) { h.shares = sharesM[1].trim(); h.value = `${sharesM[2]} 亿`; }

    const pctM = holdingsSection.match(/Holding %:\s*([\d.]+)%/);
    if (pctM) h.pct = `${pctM[1]}%`;

    const chg1dM = holdingsSection.match(/Holding Value Chg \(1d\):\s*([+-][\d.]+)\s*亿元/);
    if (chg1dM) h.chg1d = `${chg1dM[1]} 亿`;

    const chg5dM = holdingsSection.match(/Holding Value Chg \(5d\):\s*([+-][\d.]+)\s*亿元/);
    if (chg5dM) h.chg5d = `${chg5dM[1]} 亿`;

    if (h.date || h.value) result.holdings = h;
  }

  return result.flowItems.length > 0 ? result : null;
}

/* ------------------------------------------------------------------ */
/*  CN Market Sentiment Parser                                         */
/* ------------------------------------------------------------------ */

export function parseCnMarketSentiment(raw: string): CnMarketSentiment | null {
  if (!raw.includes("CN/HK Market Sentiment") && !raw.includes("Market sentiment data not applicable")) return null;

  const result: CnMarketSentiment = {
    source: 'akshare',
    symbol: '',
    sectors: [],
    lhb: null,
    topStocks: [],
  };

  const hdrMatch = raw.match(/=== CN\/HK Market Sentiment:\s*(.+?)\s*===/);
  if (hdrMatch) result.symbol = hdrMatch[1].trim();

  // Parse sector flow: "  industry_name: +X.XX 亿元 (XX.X%)"
  const sectorSection = raw.split('--- Dragon Tiger Board')[0] || '';
  const inflowIdx = sectorSection.indexOf('Top 5 Inflows');
  const outflowIdx = sectorSection.indexOf('Top 5 Outflows');
  if (inflowIdx >= 0) {
    const section = outflowIdx >= 0 ? sectorSection.slice(inflowIdx, outflowIdx) : sectorSection.slice(inflowIdx);
    const matches = section.matchAll(/^\s+(.+?):\s*\+([\d.]+)\s*亿元\s*\(([\d.]+)%\)/gm);
    for (const m of matches) {
      result.sectors.push({ name: m[1].trim(), netFlow: `+${m[2]} 亿`, pct: `${m[3]}%`, type: 'inflow' });
    }
  }
  if (outflowIdx >= 0) {
    const section = sectorSection.slice(outflowIdx);
    const matches = section.matchAll(/^\s+(.+?):\s*([+-]?[\d.]+)\s*亿元\s*\(([\d.]+)%\)/gm);
    for (const m of matches) {
      result.sectors.push({ name: m[1].trim(), netFlow: `${m[2]} 亿`, pct: `${m[3]}%`, type: 'outflow' });
    }
  }

  // Parse Dragon Tiger Board
  const lhbSection = raw.split('--- Dragon Tiger Board')[1]?.split('--- Top Capital Flow Leaders')[0] || '';
  if (lhbSection && lhbSection.includes('LHB Appearances')) {
    const appsM = lhbSection.match(/LHB Appearances:\s*(\d+)/);
    const buyM = lhbSection.match(/Cumulative Buy:\s*([\d.]+)\s*亿元/);
    const sellM = lhbSection.match(/Cumulative Sell:\s*([\d.]+)\s*亿元/);

    const recent: CnMarketSentiment['lhb']['recent'] = [];
    const recentMatches = lhbSection.matchAll(/\[([^\]]+)\]\s*Close:\s*([\d.]+)\s*—\s*(.+)/g);
    for (const m of recentMatches) {
      recent.push({ date: m[1].trim(), close: m[2], reason: m[3].trim() });
    }

    result.lhb = {
      appearances: appsM ? parseInt(appsM[1]) : 0,
      cumulativeBuy: buyM ? `${buyM[1]} 亿` : '',
      cumulativeSell: sellM ? `${sellM[1]} 亿` : '',
      recent,
    };
  }

  // Parse top capital flow leaders
  const leadersSection = raw.split('--- Top Capital Flow Leaders')[1] || '';
  if (leadersSection) {
    const leaderMatches = leadersSection.matchAll(
      /^\s+(\d+)\s+(\S+)\s*:\s*([\d.]+)\s*\(([+-][\d.]+)%\)\s*\|\s*Net:\s*\+([\d.]+)\s*亿元\s*\(([\d.]+)%\)/gm
    );
    for (const m of leaderMatches) {
      result.topStocks.push({
        code: m[1],
        name: m[2],
        price: m[3],
        change: `${m[4]}%`,
        netFlow: `+${m[5]} 亿`,
        pct: `${m[6]}%`,
      });
    }
  }

  return result.sectors.length > 0 || result.lhb || result.topStocks.length > 0 ? result : null;
}

/* ------------------------------------------------------------------ */
/*  US Fundamentals Parser                                             */
/* ------------------------------------------------------------------ */

export function parseUsFundamentals(raw: string): UsFundamentals | null {
  if (!raw.includes("US Fundamentals")) return null;

  const result: UsFundamentals = {
    source: 'yfinance',
    symbol: '',
    analystTargets: null,
    recommendations: [],
    insiderTrades: [],
    institutionalHolders: [],
    ownershipSummary: [],
    earnings: [],
    secFilings: [],
  };

  const hdrMatch = raw.match(/=== US Fundamentals:\s*(.+?)\s*===/);
  if (hdrMatch) result.symbol = hdrMatch[1].trim();

  // Analyst Targets
  const targetSection = raw.match(/--- Analyst Consensus ---\n([\s\S]*?)(?:\n---|\n$)/);
  if (targetSection) {
    const t: UsFundamentals['analystTargets'] = { current: '', low: '', mean: '', median: '', high: '', premium: '' };
    const cm = targetSection[1].match(/Current Price:\s*\$?([\d.]+)/);
    if (cm) t.current = cm[1];
    const lm = targetSection[1].match(/Target Low:\s*\$?([\d.]+)/);
    if (lm) t.low = lm[1];
    const mm = targetSection[1].match(/Target Mean:\s*\$?([\d.]+)\s*\(([+-][\d.]+)%\)/);
    if (mm) { t.mean = mm[1]; t.premium = `${mm[2]}%`; }
    const medm = targetSection[1].match(/Target Median:\s*\$?([\d.]+)/);
    if (medm) t.median = medm[1];
    const hm = targetSection[1].match(/Target High:\s*\$?([\d.]+)/);
    if (hm) t.high = hm[1];
    if (t.current) result.analystTargets = t;
  }

  // Recommendations
  const recSection = raw.match(/--- Analyst Recommendations ---\n([\s\S]*?)(?:\n---|\n$)/);
  if (recSection) {
    for (const rc of recSection[1].matchAll(/^\s+(\w+):\s*(\d+)/gm)) {
      result.recommendations.push({ label: rc[1], count: parseInt(rc[2]) });
    }
  }

  // Insider Transactions
  const insiderSection = raw.match(/--- Recent Insider Transactions ---\n([\s\S]*?)(?:\n---|\n$)/);
  if (insiderSection) {
    for (const ic of insiderSection[1].matchAll(
      /\[(.+?)\]\s*(.+?):\s*(.+?)\s*—\s*Shares:\s*([\d,]+)(?:.*?\$?([\d,]+))?/gm
    )) {
      result.insiderTrades.push({
        date: ic[1], name: ic[2].trim(), transaction: ic[3].trim(),
        shares: ic[4], value: ic[5] || '',
      });
    }
  }

  // Institutional Holders
  const instSection = raw.match(/--- Top Institutional Holders ---\n([\s\S]*?)(?:\n---|\n$)/);
  if (instSection) {
    for (const ih of instSection[1].matchAll(
      /^\s+(.+?):\s*([\d,]+)\s*shares(?:\s*\(([\d.]+)%\))?/gm
    )) {
      result.institutionalHolders.push({
        holder: ih[1].trim(), shares: ih[2],
        pct: ih[3] ? `${ih[3]}%` : '',
      });
    }
  }

  // Ownership Summary
  const ownSection = raw.match(/--- Ownership Summary ---\n([\s\S]*?)(?:\n---|\n$)/);
  if (ownSection) {
    for (const ol of ownSection[1].matchAll(/^\s+(.+?):\s*(.+)/gm)) {
      result.ownershipSummary.push({ label: ol[1].trim(), value: ol[2].trim() });
    }
  }

  // Earnings Calendar
  const earnSection = raw.match(/--- Earnings Calendar ---\n([\s\S]*?)(?:\n---|\n$)/);
  if (earnSection) {
    const entries = earnSection[1].split(/\n(?=\s+(?:Upcoming|\[))/);
    for (const entry of entries) {
      const e: UsFundamentals['earnings'][0] = {
        date: '', type: 'past', epsEstimate: '', epsActual: '', surprise: '',
      };
      const isUpcoming = entry.includes('Upcoming');
      e.type = isUpcoming ? 'upcoming' : 'past';
      const dm = entry.match(isUpcoming ? /(\d{4}-\d{2}-\d{2})/ : /\[(\d{4}-\d{2}-\d{2})\]/);
      if (dm) e.date = dm[1];
      const estm = entry.match(/EPS Estimate:\s*\$?([\d.]+)/);
      if (estm) e.epsEstimate = estm[1];
      const actm = entry.match(/EPS Actual:\s*\$?([\d.]+)/);
      if (actm) e.epsActual = actm[1];
      const surpm = entry.match(/Surprise:\s*([+-][\d.]+)%/);
      if (surpm) e.surprise = surpm[1];
      if (e.date) result.earnings.push(e);
    }
  }

  // SEC Filings
  const secSection = raw.match(/--- Recent SEC Filings ---\n([\s\S]*?)(?:\n===$|\n$)/);
  if (secSection) {
    for (const sf of secSection[1].matchAll(
      /\[(.+?)\]\s*(.+?)(?::\s*(.*?))?(?:\s*\((https?:\/\/[^\s)]+)\))?$/gm
    )) {
      result.secFilings.push({
        date: sf[1], type: sf[2].trim(),
        title: sf[3] ? sf[3].trim().slice(0, 100) : '',
        url: sf[4] || '',
      });
    }
  }

  return result.analystTargets || result.earnings.length > 0 || result.insiderTrades.length > 0
    ? result : null;
}
