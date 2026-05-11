/* ------------------------------------------------------------------ */
/*  Parsers — extract structured data from raw tool output            */
/* ------------------------------------------------------------------ */

export interface MarketData {
  source: 'futu' | 'yfinance' | 'unknown';
  name: string;
  symbol: string;
  asOf: string;
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

  const noteMatch = raw.match(/^\(Note:[^)]+\)/m);
  if (noteMatch) result.note = noteMatch[0];

  const querySections = raw.split(/--- Query:.*?---/);
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

  const countMatch = raw.match(/Articles:\s*(\d+)/);
  if (countMatch) result.articleCount = parseInt(countMatch[1]);

  const catRegex = /---\s*(.+?)\s*\((\d+)\s*articles?\)\s*---/g;
  const catSections: { start: number; end: number; name: string; count: number }[] = [];
  let catMatch;
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

  for (const cs of catSections) {
    const sectionText = raw.slice(cs.start, cs.end);
    const articles: SentimentNews['categories'][0]['articles'] = [];
    const articleBlocks = sectionText.split(/\n(?=\[\d{4}-)/);
    for (const block of articleBlocks) {
      const dateMatch = block.match(/^\[([^\]]+)\]\s*(.+)/);
      if (!dateMatch) continue;
      const sourceMatch = block.match(/Source:\s*(.+?)\s*\|?\s*(https?:\/\/\S+)?/);
      const summaryMatch = block.match(/Summary:\s*(.+?)(?:\n|$)/);
      articles.push({
        date: dateMatch[1],
        headline: dateMatch[2],
        source: sourceMatch ? sourceMatch[1].trim() : '',
        url: sourceMatch && sourceMatch[2] ? sourceMatch[2].trim() : '',
        summary: summaryMatch ? summaryMatch[1].trim() : '',
      });
    }
    if (articles.length) {
      result.categories.push({ name: cs.name, count: cs.count, articles });
    }
  }

  return result.categories.length > 0 ? result : null;
}
