import { useState, useEffect } from "react";
import { ExternalLink, FileText, Loader2, TrendingUp, TrendingDown, Search, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { fetchWithFallback, MOCK_NEWS, MOCK_DISCLOSURES, type NewsItem, type Disclosure } from "@/lib/api";
import { POPULAR_STOCKS } from "@/lib/stocks";

const GRADE_COLOR: Record<string, string> = {
  A: "bg-emerald-600", B: "bg-blue-600", C: "bg-amber-600", D: "bg-rose-600",
};

function ScoreBar({ score }: { score: number }) {
  const pct = Math.min(Math.abs(score) / 2.0 * 100, 100);
  const pos  = score >= 0;
  return (
    <div className="flex items-center gap-2">
      <span className={`font-sans text-xs font-bold min-w-[44px] ${pos ? "text-emerald-400" : "text-rose-400"}`}>
        {score > 0 ? "+" : ""}{score.toFixed(2)}
      </span>
      <div className="w-20 h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${pos ? "bg-emerald-500" : "bg-rose-500"}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}


// ── 애니메이션 점 컴포넌트 ───────────────────────────────
function AnimatedDots() {
  const [dots, setDots] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setDots(d => (d + 1) % 4), 400);
    return () => clearInterval(t);
  }, []);
  return <span className="text-blue-400">{".".repeat(dots)}</span>;
}

export default function News() {
  const [selectedSymbol, setSelectedSymbol] = useState("005930.KS");
  const [searchQ,        setSearchQ]        = useState("");
  const [showDropdown,   setShowDropdown]   = useState(false);
  const [news,           setNews]           = useState<NewsItem[]>(MOCK_NEWS);
  const [disclosures,    setDisclosures]     = useState<Disclosure[]>(MOCK_DISCLOSURES);
  const [sentiment,      setSentiment]       = useState<any>(null);
  const [loading,        setLoading]         = useState(false);

  const selectedStock = POPULAR_STOCKS.find(s => s.symbol === selectedSymbol);

  // 검색 필터링
  const filteredStocks = searchQ.trim()
    ? POPULAR_STOCKS.filter(s =>
        s.name.toLowerCase().includes(searchQ.toLowerCase()) ||
        s.symbol.toLowerCase().includes(searchQ.toLowerCase())
      ).slice(0, 10)
    : POPULAR_STOCKS.slice(0, 10);

  const selectStock = (symbol: string, name: string) => {
    setSelectedSymbol(symbol);
    setSearchQ(name);
    setShowDropdown(false);
  };

  const search = async () => {
    if (!selectedSymbol) return;
    setLoading(true);
    const [nRes, dRes] = await Promise.all([
      fetchWithFallback<{ ok: boolean; data: NewsItem[]; sentiment: any }>(
        `/news/${encodeURIComponent(selectedSymbol)}?limit=20`, {}, { ok: false, data: MOCK_NEWS, sentiment: null }
      ),
      fetchWithFallback<{ ok: boolean; data: Disclosure[] }>(
        `/disclosure/${encodeURIComponent(selectedStock?.name || "")}?limit=10`, {}, { ok: false, data: MOCK_DISCLOSURES }
      ),
    ]);
    setNews(nRes.ok ? nRes.data : MOCK_NEWS);
    setSentiment(nRes.sentiment || null);
    setDisclosures(dRes.ok ? dRes.data : MOCK_DISCLOSURES);
    setLoading(false);
  };

  const getLabel = (n: any) => n.sentimentLabel ?? n.sentiment_label ?? "";
  const posNews = news.filter(n => getLabel(n) === "positive");
  const negNews = news.filter(n => getLabel(n) === "negative");
  const avgScore = news.length
    ? (news.reduce((s, n) => s + ((n.sentimentScore ?? (n.sentimentScore ?? n.sentiment_score ?? 0) ?? 0)), 0) / news.length).toFixed(2)
    : "0.00";

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">뉴스 & 공시</h2>
        <p className="text-sm text-slate-500 mt-1">CLOVA Studio AI가 기사 원문을 분석해 감성을 판단합니다.</p>
        <p className="text-xs text-slate-600 mt-1">※ AI 분석 결과는 100% 정확하지 않을 수 있습니다.</p>
      </div>

      {/* 종목 검색 + 조회 버튼 */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <div className="flex items-center bg-slate-800 border border-slate-700 rounded-lg px-3 focus-within:border-blue-500 transition-colors">
            <Search className="w-4 h-4 text-slate-500 shrink-0" />
            <input
              value={searchQ}
              onChange={e => { setSearchQ(e.target.value); setShowDropdown(true); }}
              onFocus={() => setShowDropdown(true)}
              onBlur={() => setTimeout(() => setShowDropdown(false), 150)}
              placeholder="종목명 또는 코드 검색 (예: 삼성전자, NVDA)"
              className="flex-1 bg-transparent px-2 py-2.5 text-sm text-slate-200 placeholder:text-slate-500 outline-none"
            />
            {searchQ && (
              <button onClick={() => { setSearchQ(""); setSelectedSymbol(""); }}
                className="text-slate-500 hover:text-slate-300">
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
          {/* 드롭다운 */}
          {showDropdown && filteredStocks.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-slate-900 border border-slate-700 rounded-lg shadow-xl z-50 max-h-60 overflow-y-auto">
              {filteredStocks.map(s => (
                <button key={s.symbol} onMouseDown={() => selectStock(s.symbol, s.name)}
                  className={`w-full flex items-center justify-between px-4 py-2.5 text-sm hover:bg-slate-800 transition-colors text-left
                    ${selectedSymbol === s.symbol ? "bg-blue-600/10 text-blue-400" : "text-slate-200"}`}>
                  <span className="font-medium">{s.name}</span>
                  <span className="text-slate-500 text-xs font-sans">{s.symbol}</span>
                </button>
              ))}
              {searchQ && POPULAR_STOCKS.filter(s =>
                s.name.toLowerCase().includes(searchQ.toLowerCase()) ||
                s.symbol.toLowerCase().includes(searchQ.toLowerCase())
              ).length > 10 && (
                <div className="px-4 py-2 text-xs text-slate-500 border-t border-slate-800">
                  더 정확한 검색어를 입력하세요
                </div>
              )}
            </div>
          )}
        </div>
        <Button onClick={search} disabled={loading || !selectedSymbol}
          className="bg-blue-600 hover:bg-blue-500 shrink-0 px-6">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "조회"}
        </Button>
      </div>

      {/* 로딩 중 */}
      {loading && (
        <div className="text-center py-20">
          <div className="text-5xl mb-5">📰</div>
          <p className="text-slate-200 font-bold text-lg">
            '{selectedStock?.name}' 뉴스 수집 중
            <AnimatedDots />
          </p>
          <p className="text-slate-500 text-sm mt-3">원문 크롤링 및 AI 감성 분석 중입니다</p>
          <p className="text-slate-600 text-xs mt-1">30초~1분 소요될 수 있습니다</p>
        </div>
      )}

      {!loading && (
        <>
          {/* 감성 요약 */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-card border border-border rounded-xl p-4">
              <div className="text-xs text-slate-400 mb-2">전체 평균 감성</div>
              <div className={`text-3xl font-bold font-sans ${Number(avgScore) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                {Number(avgScore) > 0 ? "+" : ""}{avgScore}
              </div>
            </div>
            <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4">
              <div className="text-xs text-slate-400 mb-2 flex items-center gap-1">
                <TrendingUp className="w-3 h-3 text-emerald-400" /> 긍정 기사
              </div>
              <div className="text-3xl font-bold font-sans text-emerald-400">{posNews.length}건</div>
            </div>
            <div className="bg-rose-500/10 border border-rose-500/20 rounded-xl p-4">
              <div className="text-xs text-slate-400 mb-2 flex items-center gap-1">
                <TrendingDown className="w-3 h-3 text-rose-400" /> 부정 기사
              </div>
              <div className="text-3xl font-bold font-sans text-rose-400">{negNews.length}건</div>
            </div>
          </div>

          {/* 신뢰도 등급 */}
          <div className="flex items-center gap-3 text-xs text-slate-500 flex-wrap">
            <span className="font-medium text-slate-400">신뢰도 등급:</span>
            {(["A","B","C","D"] as const).map(g => (
              <span key={g} className="flex items-center gap-1.5">
                <span className={`px-1.5 py-0.5 rounded text-white font-bold text-[10px] ${GRADE_COLOR[g]}`}>{g}</span>
                <span>{{A:"원문+제목 CLOVA",B:"제목만 CLOVA",C:"KNU 사전",D:"분석불가"}[g]}</span>
              </span>
            ))}
          </div>

          <Tabs defaultValue="positive">
            <TabsList className="bg-slate-800 border border-border">
              <TabsTrigger value="all"      className="data-[state=active]:bg-blue-600 data-[state=active]:text-white text-slate-400">전체 ({news.length})</TabsTrigger>
              <TabsTrigger value="positive" className="data-[state=active]:bg-emerald-600 data-[state=active]:text-white text-slate-400">긍정 ({posNews.length})</TabsTrigger>
              <TabsTrigger value="negative" className="data-[state=active]:bg-rose-600 data-[state=active]:text-white text-slate-400">부정 ({negNews.length})</TabsTrigger>
              <TabsTrigger value="disclosure" className="data-[state=active]:bg-blue-600 data-[state=active]:text-white text-slate-400">공시 ({disclosures.length})</TabsTrigger>
            </TabsList>

            {(["all","positive","negative"] as const).map(tab => {
              const list = tab === "all" ? news : tab === "positive" ? posNews : negNews;
              return (
                <TabsContent key={tab} value={tab} className="mt-4">
                  <NewsList items={list} />
                </TabsContent>
              );
            })}

            <TabsContent value="disclosure" className="mt-4">
              <div className="bg-card border border-border rounded-xl overflow-hidden divide-y divide-border">
                {disclosures.length === 0 ? (
                  <div className="py-12 text-center text-slate-500 text-sm">공시 결과가 없습니다.</div>
                ) : disclosures.map((d, i) => (
                  <a key={i} href={d.url !== "#" ? d.url : undefined} target="_blank" rel="noreferrer"
                    className="p-4 hover:bg-slate-800/40 transition-colors flex items-center gap-4 block">
                    <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center shrink-0">
                      <FileText className="w-4 h-4 text-blue-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-200 font-medium truncate">{d.title}</p>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-xs text-slate-500">{d.date}</span>
                        <span className="text-[10px] bg-slate-800 border border-slate-700 text-slate-400 rounded px-1.5 py-0.5">{d.type}</span>
                      </div>
                    </div>
                    {d.url !== "#" && <ExternalLink className="w-3.5 h-3.5 text-slate-600 shrink-0" />}
                  </a>
                ))}
              </div>
            </TabsContent>
          </Tabs>
        </>
      )}
    </div>
  );
}

function NewsList({ items }: { items: NewsItem[] }) {
  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden divide-y divide-border">
      {items.length === 0 ? (
        <div className="py-12 text-center text-slate-500 text-sm">기사가 없습니다.</div>
      ) : items.map((item, i) => {
        const pos = (item.sentimentLabel ?? item.sentiment_label) === "positive";
        return (
          <a key={i} href={item.url !== "#" ? item.url : undefined} target="_blank" rel="noreferrer"
            className="p-4 hover:bg-slate-800/40 transition-colors flex items-start gap-4 block">
            <div className={`shrink-0 w-12 h-12 rounded-lg flex flex-col items-center justify-center border
              ${pos ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border-rose-500/20"}`}>
              {item.grade && (
                <span className={`text-[9px] font-bold px-1 rounded text-white mb-0.5 ${GRADE_COLOR[item.grade] || "bg-slate-600"}`}>{item.grade}</span>
              )}
              <span className="text-xs font-sans font-bold">{((item.sentimentScore ?? (item.sentimentScore ?? item.sentiment_score ?? 0) ?? 0)) > 0 ? "+" : ""}{((item.sentimentScore ?? (item.sentimentScore ?? item.sentiment_score ?? 0) ?? 0)).toFixed(1)}</span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm text-slate-200 font-medium leading-snug line-clamp-2 flex-1">{item.title}</p>
                {item.url !== "#" && <ExternalLink className="w-3.5 h-3.5 text-slate-600 shrink-0 mt-0.5" />}
              </div>
              <div className="flex items-center gap-3 mt-2 flex-wrap">
                {item.source && <span className="text-xs text-slate-500">{item.source}</span>}
                <span className="text-xs text-slate-600">{(item.published ?? item.date ?? "")}</span>
                <ScoreBar score={(item.sentimentScore ?? (item.sentimentScore ?? item.sentiment_score ?? 0) ?? 0)} />
              </div>
              {(() => { const r = item.sentimentReason ?? item.reason; return r && !r.includes("KNU"); })() && (
                <p className="text-xs text-slate-500 mt-1">💡 {(item.sentimentReason ?? item.reason)}</p>
              )}
            </div>
          </a>
        );
      })}
    </div>
  );
}
