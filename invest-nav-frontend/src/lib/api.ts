// Flask API 기본 URL
// 로컬 개발: /api (vite proxy)
// 시연 환경: /cau19/py
const IS_DEV = import.meta.env.DEV;
const BASE = IS_DEV ? "/api" : "/cau19/py";

export async function fetchWithFallback<T>(
  url: string,
  options: RequestInit,
  fallback: T
): Promise<T> {
  try {
    const fullUrl = url.startsWith("http") ? url : `${BASE}${url}`;
    const res = await fetch(fullUrl, {
      ...options,
      headers: { "Content-Type": "application/json", ...options.headers },
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return await res.json();
  } catch (error) {
    console.warn(`API failed for ${url}:`, error);
    return fallback;
  }
}

export async function postJSON<T>(url: string, body: unknown, fallback: T): Promise<T> {
  return fetchWithFallback<T>(url, {
    method: "POST",
    body: JSON.stringify(body),
  }, fallback);
}

// ── Mock 데이터 ──────────────────────────────────────────
export const MOCK_MACRO = {
  kospi:   { price: "8,228.70", change_pct: "+2.25%" },
  nasdaq:  { price: "26,656.18", change_pct: "+1.19%" },
  sp500:   { price: "7,519.12", change_pct: "+0.61%" },
  usd_krw: { price: "1,496.48", change_pct: "-1.21%" },
  gold:    { price: "4,525.50", change_pct: "+0.56%" },
  wti:     { price: "89.91",    change_pct: "-4.24%" },
};

export const MOCK_ANALYSIS = {
  analysis: "AI 반도체 중심 랠리 지속. 외국인 자금 유입 가속화되며 KOSPI 강세 유지 전망."
};

export const MOCK_NEWS: NewsItem[] = [
  { title: "삼성전자 HBM 테스트 통과 임박 '기대감 고조'", url: "#", published: "10분 전", sentiment_score: 1.8, sentiment_label: "positive", source: "한국경제", grade: "A", reason: "HBM 수혜 기대" },
  { title: "외국인 코스피 1.5조 순매수... 반도체 집중매수", url: "#", published: "1시간 전", sentiment_score: 1.5, sentiment_label: "positive", source: "매일경제", grade: "A", reason: "외국인 매수세 지속" },
  { title: "환율 폭등 우려... 수출 기업 타격 불가피", url: "#", published: "2시간 전", sentiment_score: -1.2, sentiment_label: "negative", source: "연합뉴스", grade: "B", reason: "환율 상승은 수출기업에 부정적" },
  { title: "애플 중국 판매 부진 심화, 아이폰 점유율 하락", url: "#", published: "3시간 전", sentiment_score: -1.5, sentiment_label: "negative", source: "서울경제", grade: "A", reason: "중국 시장 점유율 하락" },
];

export const MOCK_DISCLOSURES = [
  { title: "연결재무제표기준영업실적(공정공시)", date: "2024-03-21", type: "실적", url: "#" },
  { title: "현금ㆍ현물배당결정", date: "2024-03-15", type: "배당", url: "#" },
];

export const MOCK_PORTFOLIO_RESULT = {
  ok: true,
  rr: { score: 5.71, raw_score: 5.71, label: "neutral", label_kr: "중립", emoji: "🟡", reward: 14.2, risk: 8.5, data_source: "5년 실제 데이터", scenarios_used: { bull: { return: 35, prob: 20 }, base: { return: 12, prob: 60 }, bear: { return: -22, prob: 20 } } },
  scenarios: [
    { scenario: "Bull", emoji: "🐂", expectedReturn: 35, probability: 20, description: "경기 호조, 금리 인하, 실적 개선", color: "#00C896" },
    { scenario: "Base", emoji: "📊", expectedReturn: 12, probability: 60, description: "현재 추세 지속, 완만한 성장", color: "#4A9EFF" },
    { scenario: "Bear", emoji: "🐻", expectedReturn: -22, probability: 20, description: "경기 침체, 금리 급등, 지정학 리스크", color: "#FF6B6B" },
  ],
  sector_alloc: { "반도체": 50, "기술": 20, "금융": 15, "에너지": 15 },
  inferred: "aggressive",
  recommendations: ["R/R Score 5.71점 — 수익과 손실이 균형 잡혀 있습니다.", "섹터 분산이 양호합니다."],
};

// ── 타입 정의 ────────────────────────────────────────────
export interface MacroIndicator { price: string; change_pct: string; }
export interface MacroData { [key: string]: MacroIndicator; }
export interface NewsItem {
  title: string;
  url: string;
  published?: string;          // 검색 뉴스
  date?: string;               // 네이버 금융 뉴스
  source?: string;
  // Flask 실제 필드명 (camelCase)
  sentimentScore?: number;
  sentimentLabel?: string;
  sentimentReason?: string;
  grade?: string;
  keywords?: string[];
  isOriginal?: boolean;
  // 하위 호환 (snake_case)
  sentiment_score?: number;
  sentiment_label?: string;
  reason?: string;
}
export interface Disclosure { title: string; date: string; type: string; url: string; }
export interface PortfolioHolding { symbol: string; name: string; weight: number; market: string; }

export const MOCK_MEMOS = [
  {
    id: 1,
    title: "삼성전자 2024년 투자 분석",
    stock: "005930.KS",
    content: JSON.stringify({ investment_thesis: "HBM 수혜 + 파운드리 반등 기대", conclusion: "목표가 9만원, 분할 매수" }),
    tags: ["반도체", "HBM", "수출"],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 2,
    title: "엔비디아 밸류에이션 점검",
    stock: "NVDA",
    content: JSON.stringify({ investment_thesis: "AI 인프라 수요 독점적 지위", risk_analysis: "중국 수출 규제 리스크" }),
    tags: ["AI", "GPU", "미국주식"],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export interface Memo {
  id: number; title: string; content: string;
  stock: string; tags: string[];
  created_at: string; updated_at: string;
}
