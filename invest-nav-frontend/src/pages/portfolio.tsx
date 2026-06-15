import { useState, useEffect } from "react";
import { Plus, Trash2, Loader2, Info, Search, X, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { postJSON, MOCK_PORTFOLIO_RESULT } from "@/lib/api";
import { POPULAR_STOCKS, STOCK_BY_DISPLAY } from "@/lib/stocks";
import { addFavorite, isFavorite, getFavorites } from "@/lib/favorites";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, RadialBarChart, RadialBar } from "recharts";

const PT_CONFIG: Record<string, { label: string; desc: string; emoji: string; color: string }> = {
  ultra_aggressive: { label: "초공격형",  desc: "단일 섹터 극도 집중 — 극고위험·극고수익", emoji: "🔥", color: "#dc2626" },
  aggressive:       { label: "공격투자형", desc: "성장주·반도체·기술 중심 — 고위험·고수익", emoji: "🚀", color: "#f97316" },
  balanced:         { label: "위험중립형", desc: "성장·방어 균형 — 중위험·중수익",          emoji: "⚖️", color: "#3b82f6" },
  conservative:     { label: "안정추구형", desc: "금융·유틸리티·배당주 중심 — 저위험·안정", emoji: "🛡️", color: "#22c55e" },
  ultra_conservative:{ label: "초안정형", desc: "ETF·채권 중심 — 극저위험·안정 수익",      emoji: "🏦", color: "#06b6d4" },
};

function fmt(krw: number) {
  if (krw >= 1e8) return `${(krw / 1e8).toFixed(1)}억원`;
  if (krw >= 1e4) return `${(krw / 1e4).toLocaleString()}만원`;
  return `${krw.toLocaleString()}원`;
}

interface Holding { symbol: string; name: string; market: string; weight: number; }

const DEFAULT_HOLDINGS: Holding[] = [
  { symbol: "NVDA",      name: "엔비디아 (NVIDIA)", market: "NASDAQ", weight: 30 },
  { symbol: "005930.KS", name: "삼성전자",           market: "KRX",    weight: 30 },
  { symbol: "000660.KS", name: "SK하이닉스",         market: "KRX",    weight: 20 },
  { symbol: "AAPL",      name: "애플 (Apple)",       market: "NASDAQ", weight: 20 },
];

const SECTOR_COLORS = ["#22c55e","#3b82f6","#f59e0b","#a855f7","#ec4899","#ef4444","#06b6d4","#84cc16"];





// ── 애니메이션 점 컴포넌트 ───────────────────────────────
function AnimatedDots() {
  const [dots, setDots] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setDots(d => (d + 1) % 4), 400);
    return () => clearInterval(t);
  }, []);
  return <span className="text-blue-400">{".".repeat(dots)}</span>;
}

// ── 백테스팅 컴포넌트 ────────────────────────────────────
function BacktestPanel({ holdings, totalAmt }: {
  holdings: { symbol: string; name: string; market: string; weight: number }[];
  totalAmt: number;
}) {
  const [startDate, setStartDate] = useState("2022-01-01");
  const [endDate,   setEndDate]   = useState(new Date().toISOString().split("T")[0]);
  const [benchmark, setBenchmark] = useState("^KS11");
  const [result,    setResult]    = useState<any>(null);
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState("");

  const BENCHMARKS = [
    { value: "^KS11", label: "KOSPI"   },
    { value: "^IXIC", label: "NASDAQ"  },
    { value: "^GSPC", label: "S&P 500" },
    { value: "^KQ11", label: "KOSDAQ"  },
  ];

  const run = async () => {
    if (!holdings.length) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const ctrl = new AbortController();
      const tid  = setTimeout(() => ctrl.abort(), 90000);
      const resp = await fetch("/api/portfolio/backtest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          holdings, start_date: startDate,
          end_date: endDate, initial_amount: totalAmt, benchmark,
        }),
        signal: ctrl.signal,
      });
      clearTimeout(tid);
      const res = await resp.json();
      if (res?.ok && res.data) setResult(res.data);
      else setError(res?.error || "분석 실패 — 다시 시도해주세요");
    } catch (e: any) {
      setError(e?.name === "AbortError"
        ? "⏱ 시간 초과(90초) — 기간을 짧게 해보세요"
        : "Flask 서버 연결 오류");
    }
    setLoading(false);
  };

  const fmtAmt = (n: number) => {
    const a = Math.abs(n), s = n >= 0 ? "+" : "-";
    if (a >= 1e8) return s + (a/1e8).toFixed(1) + "억원";
    if (a >= 1e4) return s + Math.round(a/1e4) + "만원";
    return s + a.toLocaleString() + "원";
  };

  return (
    <div className="mt-6 bg-card border border-border rounded-xl p-5">
      <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
        📈 백테스팅
        <span className="text-xs text-slate-500 font-normal">과거 데이터로 포트폴리오 성과를 검증합니다</span>
      </h3>

      {/* 설정 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div>
          <label className="text-xs text-slate-400 mb-1 block">시작일</label>
          <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500" />
        </div>
        <div>
          <label className="text-xs text-slate-400 mb-1 block">종료일</label>
          <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500" />
        </div>
        <div>
          <label className="text-xs text-slate-400 mb-1 block">벤치마크</label>
          <select value={benchmark} onChange={e => setBenchmark(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500">
            {BENCHMARKS.map(b => <option key={b.value} value={b.value}>{b.label}</option>)}
          </select>
        </div>
        <div className="flex items-end">
          <button type="button" onClick={run} disabled={loading || !holdings.length}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white text-sm font-semibold rounded-lg px-4 py-2 transition-colors">
            {loading ? <><Loader2 className="w-4 h-4 animate-spin mr-2 inline" />분석 중...</> : "▶ 백테스트 실행"}
          </button>
        </div>
      </div>

      {error && (
        <p className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg p-3 mb-3">
          ❌ {error}
        </p>
      )}

      {loading && (
        <div className="text-center py-8 text-slate-400 text-sm">
          <div className="text-2xl mb-2 animate-spin inline-block">⏳</div>
          <p>yfinance로 과거 데이터 수집 중입니다<AnimatedDots /></p>
          <p className="text-xs text-slate-500 mt-1">30초~1분 소요됩니다</p>
        </div>
      )}

      {result && !loading && (
        <div className="space-y-4">
          {/* 주요 지표 4개 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {(() => {
              const tr  = Number(result.totalReturn);
              const ar  = Number(result.annualizedReturn);
              const mdd = Number(result.maxDrawdown);
              const sr  = Number(result.sharpeRatio);
              return [
                { label: "총 수익률",     val: (tr >= 0 ? "+" : "") + tr.toFixed(2) + "%",   cls: tr >= 0 ? "text-emerald-400" : "text-rose-400" },
                { label: "연환산 수익률", val: (ar >= 0 ? "+" : "") + ar.toFixed(2) + "%",   cls: ar >= 0 ? "text-emerald-400" : "text-rose-400" },
                { label: "최대 낙폭",     val: "-" + mdd.toFixed(2) + "%",                   cls: "text-rose-400" },
                { label: "샤프 비율",     val: sr.toFixed(2),                                cls: sr >= 1 ? "text-emerald-400" : "text-amber-400" },
              ];
            })().map(({ label, val, cls }) => (
              <div key={label} className="bg-slate-800/60 border border-slate-700 rounded-xl p-3 text-center">
                <div className="text-xs text-slate-400 mb-1">{label}</div>
                <div className={"text-lg font-bold font-sans " + cls}>{val}</div>
              </div>
            ))}
          </div>

          {/* 포트폴리오 vs 벤치마크 */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4">
              <div className="text-xs text-blue-400 font-semibold mb-2">📊 내 포트폴리오</div>
              <div className={"text-2xl font-bold font-sans " + (Number(result.totalReturn) >= 0 ? "text-emerald-400" : "text-rose-400")}>
                {Number(result.totalReturn) >= 0 ? "+" : ""}{Number(result.totalReturn).toFixed(2)}%
              </div>
              <div className="text-xs text-slate-400 mt-1">최종 잔액: {Number(result.finalValue).toLocaleString()}원</div>
              {totalAmt > 0 && (
                <div className={"text-xs font-sans mt-1 " + (Number(result.totalReturn) >= 0 ? "text-emerald-400" : "text-rose-400")}>
                  {fmtAmt(Number(result.finalValue) - totalAmt)}
                </div>
              )}
            </div>
            <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-4">
              <div className="text-xs text-slate-400 font-semibold mb-2">
                📈 {BENCHMARKS.find(b => b.value === benchmark)?.label}
              </div>
              <div className={"text-2xl font-bold font-sans " + (Number(result.benchmarkReturn) >= 0 ? "text-emerald-400" : "text-rose-400")}>
                {Number(result.benchmarkReturn) >= 0 ? "+" : ""}{Number(result.benchmarkReturn).toFixed(2)}%
              </div>
              <div className={"text-xs font-semibold mt-2 " + (Number(result.totalReturn) >= Number(result.benchmarkReturn) ? "text-emerald-400" : "text-rose-400")}>
                {Number(result.totalReturn) >= Number(result.benchmarkReturn)
                  ? "▲ +" + (Number(result.totalReturn) - Number(result.benchmarkReturn)).toFixed(2) + "%p 초과"
                  : "▼ " + (Number(result.totalReturn) - Number(result.benchmarkReturn)).toFixed(2) + "%p 미달"}
              </div>
            </div>
          </div>

          {/* 추가 지표 */}
          <div className="grid grid-cols-3 gap-3 text-center text-sm">
            <div className="bg-slate-800/40 rounded-lg p-3">
              <div className="text-xs text-slate-400">연간 변동성</div>
              <div className="font-bold font-sans text-white">{Number(result.volatility).toFixed(1)}%</div>
            </div>
            <div className="bg-slate-800/40 rounded-lg p-3">
              <div className="text-xs text-slate-400">승률</div>
              <div className="font-bold font-sans text-white">{Number(result.winRate).toFixed(1)}%</div>
            </div>
            <div className="bg-slate-800/40 rounded-lg p-3">
              <div className="text-xs text-slate-400">데이터 기간</div>
              <div className="font-bold font-sans text-white">{Array.isArray(result.dataPoints) ? result.dataPoints.length : result.dataPoints}일</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── 즐겨찾기 추가 컴포넌트 ───────────────────────────────
function FavoriteAdder({ holdings }: { holdings: { symbol: string; name: string; market: string; weight: number }[] }) {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [saved, setSaved]       = useState(false);

  const toggle = (symbol: string) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(symbol)) next.delete(symbol);
      else next.add(symbol);
      return next;
    });
    setSaved(false);
  };

  const saveAll = () => {
    holdings.forEach(h => addFavorite({ symbol: h.symbol, name: h.name, market: h.market }));
    setSelected(new Set(holdings.map(h => h.symbol)));
    setSaved(true);
  };

  const saveSelected = () => {
    holdings.filter(h => selected.has(h.symbol))
      .forEach(h => addFavorite({ symbol: h.symbol, name: h.name, market: h.market }));
    setSaved(true);
  };

  return (
    <div className="bg-slate-800/40 border border-slate-700 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide flex items-center gap-1.5">
          <Star className="w-3.5 h-3.5 text-amber-400" /> 즐겨찾기에 추가
        </h3>
        <div className="flex gap-2">
          <button onClick={saveSelected} disabled={selected.size === 0}
            className="text-xs px-3 py-1 bg-blue-600/20 text-blue-400 border border-blue-500/30 rounded-lg hover:bg-blue-600/30 disabled:opacity-40 transition-colors">
            선택 추가
          </button>
          <button onClick={saveAll}
            className="text-xs px-3 py-1 bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-lg hover:bg-amber-500/30 transition-colors">
            전체 추가
          </button>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        {holdings.map(h => {
          const fav  = isFavorite(h.symbol);
          const sel  = selected.has(h.symbol);
          return (
            <button key={h.symbol} onClick={() => toggle(h.symbol)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs border transition-colors
                ${fav ? "bg-amber-500/10 text-amber-400 border-amber-500/30" :
                  sel ? "bg-blue-500/10 text-blue-400 border-blue-500/30" :
                        "bg-slate-800 text-slate-400 border-slate-700 hover:border-slate-500"}`}>
              <Star className={`w-3 h-3 ${fav || sel ? "fill-current" : ""}`} />
              {h.name}
            </button>
          );
        })}
      </div>
      {saved && (
        <p className="text-xs text-emerald-400 mt-2">✅ 즐겨찾기에 추가됐어요! 알림 버튼에서 확인하세요.</p>
      )}
    </div>
  );
}

// ── 검색 가능한 종목 선택 컴포넌트 ──────────────────────
function StockSearchInput({
  value, displayName, onSelect, onRemove
}: {
  value: string;
  displayName: string;
  onSelect: (symbol: string, name: string, market: string) => void;
  onRemove: () => void;
}) {
  const [q, setQ] = useState(displayName);
  const [open, setOpen] = useState(false);

  const filtered = q.trim()
    ? POPULAR_STOCKS.filter(s =>
        s.name.toLowerCase().includes(q.toLowerCase()) ||
        s.symbol.toLowerCase().includes(q.toLowerCase())
      ).slice(0, 8)
    : POPULAR_STOCKS.slice(0, 8);

  return (
    <div className="flex items-center gap-2">
      <div className="relative flex-1">
        <div className="flex items-center bg-slate-900 border border-slate-700 rounded-lg px-2 focus-within:border-blue-500 transition-colors h-8">
          <Search className="w-3 h-3 text-slate-500 shrink-0" />
          <input
            value={q}
            onChange={e => { setQ(e.target.value); setOpen(true); }}
            onFocus={() => setOpen(true)}
            onBlur={() => setTimeout(() => setOpen(false), 150)}
            className="flex-1 bg-transparent px-1.5 text-xs text-slate-200 placeholder:text-slate-500 outline-none"
            placeholder="종목 검색..."
          />
          {q && (
            <button onMouseDown={() => { setQ(""); setOpen(true); }}
              className="text-slate-500 hover:text-slate-300 transition-colors ml-1 shrink-0"
              title="종목명 지우기">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
        {open && filtered.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-slate-900 border border-slate-700 rounded-lg shadow-xl z-50 max-h-48 overflow-y-auto">
            {filtered.map(s => (
              <button key={s.symbol}
                onMouseDown={() => { onSelect(s.symbol, s.name, s.market); setQ(s.name); setOpen(false); }}
                className={`w-full flex items-center justify-between px-3 py-2 text-xs hover:bg-slate-800 transition-colors text-left
                  ${value === s.symbol ? "bg-blue-600/10 text-blue-400" : "text-slate-200"}`}>
                <span className="font-medium">{s.name}</span>
                <span className="text-slate-500 font-sans">{s.symbol}</span>
              </button>
            ))}
          </div>
        )}
      </div>
      {/* 휴지통 — 종목 칸 삭제 */}
      <button onClick={onRemove}
        className="text-slate-600 hover:text-rose-400 transition-colors shrink-0"
        title="종목 삭제">
        <Trash2 className="w-4 h-4" />
      </button>
    </div>
  );
}

export default function Portfolio() {
  const [holdings, setHoldings]     = useState<Holding[]>(DEFAULT_HOLDINGS);
  const [totalAmt, setTotalAmt]     = useState(10_000_000);
  const [result, setResult]         = useState<any>(null);
  const [loading, setLoading]       = useState(false);
  const [showRR, setShowRR]         = useState(false);
  const [error, setError]           = useState("");

  const totalW = holdings.reduce((s, h) => s + h.weight, 0);

  const updateWeight = (idx: number, w: number) => {
    setHoldings(prev => prev.map((h, i) => i === idx ? { ...h, weight: Math.max(0, Math.min(100, w)) } : h));
  };
  const removeHolding = (idx: number) => setHoldings(prev => prev.filter((_, i) => i !== idx));
  const addHolding = () => {
    const used = new Set(holdings.map(h => h.symbol));
    const next = POPULAR_STOCKS.find(s => !used.has(s.symbol));
    if (next) setHoldings(prev => [...prev, { ...next, weight: 0 }]);
  };

  const analyze = async () => {
    if (Math.abs(totalW - 100) > 0.5) {
      setError(`비중 합계가 ${totalW}%입니다. 100%로 맞춰주세요.`);
      return;
    }
    setError("");
    setLoading(true);
    const res = await postJSON("/portfolio/analyze", { holdings }, MOCK_PORTFOLIO_RESULT);
    setResult(res);
    setLoading(false);
  };

  const rr = result?.rr;
  const pt = PT_CONFIG[result?.inferred] || PT_CONFIG.balanced;
  const scoreColor = rr ? (rr.score >= 7 ? "#00C896" : rr.score >= 5 ? "#4A9EFF" : rr.score >= 3 ? "#FFA500" : "#FF6B6B") : "#4A9EFF";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">포트폴리오 분석</h2>
        <p className="text-sm text-slate-500 mt-1">모의 포트폴리오를 구성하고 R/R Score · 시나리오 · 투자 유형을 분석합니다.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* 입력 패널 */}
        <div className="lg:col-span-2 space-y-4">
          {/* 투자금액 */}
          <div className="bg-card border border-border rounded-xl p-5">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">💰 총 투자금액</h3>
            <input
              type="number"
              value={totalAmt}
              onChange={e => setTotalAmt(Number(e.target.value))}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white font-sans text-sm focus:outline-none focus:border-blue-500"
            />
            <p className="text-xs text-slate-500 mt-1">≈ {fmt(totalAmt)}</p>
          </div>

          {/* 종목 구성 */}
          <div className="bg-card border border-border rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-300">🎯 구성 종목 & 비중</h3>
              <span className={`text-xs font-sans font-bold ${Math.abs(totalW - 100) < 0.5 ? "text-emerald-400" : "text-amber-400"}`}>
                합계 {totalW}%
              </span>
            </div>

            {holdings.map((h, idx) => (
              <div key={idx} className="bg-slate-800/60 border border-slate-700 rounded-lg p-3 space-y-2">
                <StockSearchInput
                  value={h.symbol}
                  displayName={h.name}
                  onSelect={(symbol, name, market) => {
                    setHoldings(prev => prev.map((item, i) =>
                      i === idx ? { ...item, symbol, name, market } : item
                    ));
                  }}
                  onRemove={() => removeHolding(idx)}
                />
                <div className="flex items-center gap-2">
                  <input
                    type="number" min={0} max={100} value={h.weight}
                    onChange={e => updateWeight(idx, Number(e.target.value))}
                    className="w-20 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white font-sans text-sm focus:outline-none focus:border-blue-500 text-center"
                  />
                  <span className="text-slate-500 text-xs">%</span>
                  {totalAmt > 0 && (
                    <span className="text-xs text-slate-500 ml-auto">≈ {fmt(Math.round(totalAmt * h.weight / 100))}</span>
                  )}
                </div>
              </div>
            ))}

            <button onClick={addHolding} className="w-full flex items-center justify-center gap-2 text-xs text-slate-400 hover:text-slate-200 border border-dashed border-slate-700 hover:border-slate-500 rounded-lg py-2.5 transition-colors">
              <Plus className="w-3.5 h-3.5" /> 종목 추가
            </button>

            {error && <p className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded p-2">{error}</p>}
          </div>

          <Button onClick={analyze} disabled={loading} className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold" size="lg">
            {loading ? <><Loader2 className="w-4 h-4 animate-spin mr-2" />분석 중...</> : "📊 분석 실행"}
          </Button>
        </div>

        {/* 결과 패널 */}
        <div className="lg:col-span-3 space-y-4">
          {!result ? (
            <div className="h-full min-h-64 flex items-center justify-center border border-dashed border-slate-700 rounded-xl">
              <div className="text-center">
                <div className="text-4xl mb-3">📊</div>
                <p className="text-slate-400 font-medium">분석을 실행하세요</p>
                <p className="text-slate-600 text-sm mt-1">종목 비중 합계를 100%로 맞추고<br />분석 실행 버튼을 누르세요.</p>
              </div>
            </div>
          ) : (
            <>
              {/* 투자 유형 배너 */}
              <div className="rounded-xl p-5 border" style={{ background: `${pt.color}15`, borderColor: `${pt.color}40` }}>
                <div className="text-[10px] text-slate-400 uppercase tracking-widest mb-1">투자 유형 분석 결과</div>
                <div className="text-2xl font-black" style={{ color: pt.color }}>{pt.emoji} {pt.label}</div>
                <div className="text-xs text-slate-400 mt-1">{pt.desc}</div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* R/R Score 게이지 */}
                <div className="bg-card border border-border rounded-xl p-5">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide">R/R Score</h3>
                    <button onClick={() => setShowRR(!showRR)} className="text-slate-500 hover:text-slate-300 transition-colors">
                      <Info className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="text-center">
                    <div className="text-5xl font-black font-sans" style={{ color: scoreColor }}>
                      {rr?.score?.toFixed(2)}
                    </div>
                    <div className="text-sm text-slate-400 mt-1">/10점 · {rr?.label_kr}</div>
                    {/* 게이지 바 */}
                    <div className="mt-4 h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${(rr?.score / 10) * 100}%`, background: scoreColor }} />
                    </div>
                    <div className="flex justify-between text-[10px] text-slate-600 mt-1">
                      <span>0</span><span>1</span><span>3</span><span>5</span><span>7</span><span>10</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2 mt-4">
                    <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-2 text-center">
                      <div className="text-xs text-slate-400">📈 기대 수익</div>
                      <div className="text-sm font-bold text-emerald-400 font-sans">+{rr?.reward?.toFixed(1)}%</div>
                      {totalAmt > 0 && <div className="text-[10px] text-slate-500">+{fmt(Math.round(totalAmt * (rr?.reward || 0) / 100))}</div>}
                    </div>
                    <div className="bg-rose-500/10 border border-rose-500/20 rounded-lg p-2 text-center">
                      <div className="text-xs text-slate-400">📉 예상 손실</div>
                      <div className="text-sm font-bold text-rose-400 font-sans">-{rr?.risk?.toFixed(1)}%</div>
                      {totalAmt > 0 && <div className="text-[10px] text-slate-500">-{fmt(Math.round(totalAmt * (rr?.risk || 0) / 100))}</div>}
                    </div>
                  </div>
                  {rr?.data_source && (
                    <p className="text-[10px] text-slate-500 mt-2 text-center">📊 {rr.data_source} 기반</p>
                  )}
                </div>

                {/* 섹터 파이차트 */}
                <div className="bg-card border border-border rounded-xl p-5">
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">섹터 배분</h3>
                  <ResponsiveContainer width="100%" height={130}>
                    <PieChart>
                      <Pie data={Object.entries(result.sector_alloc || {}).map(([name, value]) => ({ name, value }))}
                        cx="50%" cy="50%" innerRadius={35} outerRadius={60} paddingAngle={2} dataKey="value">
                        {Object.keys(result.sector_alloc || {}).map((_, i) => (
                          <Cell key={i} fill={SECTOR_COLORS[i % SECTOR_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(v: any) => `${v}%`} contentStyle={{ background: "#1E2130", border: "1px solid #2D3142", borderRadius: "8px", fontSize: "11px" }} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="space-y-1 mt-2">
                    {Object.entries(result.sector_alloc || {}).map(([name, value], i) => (
                      <div key={name} className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-1.5">
                          <div className="w-2 h-2 rounded-full" style={{ background: SECTOR_COLORS[i % SECTOR_COLORS.length] }} />
                          <span className="text-slate-400">{name}</span>
                        </div>
                        <span className="text-slate-300 font-sans">{String(value)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* R/R 설명 토글 */}
              {showRR && (
                <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-4 text-xs text-slate-300 space-y-2">
                  <p className="font-semibold text-white">📖 R/R Score란?</p>
                  <p>기대 수익을 기대 손실로 나눈 비율 (0~10점)</p>
                  <div className="grid grid-cols-3 gap-2 mt-2">
                    {[["🟢 7~10점", "매력적", "#00C896"], ["🟡 3~7점", "중립", "#FFA500"], ["🔴 0~3점", "비매력적", "#FF6B6B"]].map(([score, label, color]) => (
                      <div key={label} className="text-center p-2 rounded-lg" style={{ background: `${color}15`, border: `1px solid ${color}30` }}>
                        <div className="text-[11px] font-bold" style={{ color }}>{score}</div>
                        <div className="text-[10px] text-slate-400">{label}</div>
                      </div>
                    ))}
                  </div>
                  {rr?.scenarios_used && (
                    <div className="grid grid-cols-3 gap-2 mt-2">
                      {[["🐂 Bull", "bull", "#00C896"], ["📊 Base", "base", "#4A9EFF"], ["🐻 Bear", "bear", "#FF6B6B"]].map(([label, key, color]) => {
                        const s = rr.scenarios_used[key];
                        return (
                          <div key={key} className="text-center p-2 rounded-lg" style={{ background: `${color}10`, border: `1px solid ${color}25` }}>
                            <div className="text-[10px] text-slate-400">{label}</div>
                            <div className="text-sm font-bold font-sans" style={{ color }}>{key !== "bear" ? "+" : ""}{s?.return}%</div>
                            <div className="text-[10px] text-slate-500">{s?.prob}%</div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* 시나리오 */}
              <div>
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">📈 시나리오 분석 {totalAmt > 0 && <span className="text-slate-600 normal-case">· {fmt(totalAmt)} 기준</span>}</h3>
                <div className="grid grid-cols-3 gap-3">
                  {(result.scenarios || []).map((sc: any) => {
                    const color = sc.color || (sc.scenario === "Bull" ? "#00C896" : sc.scenario === "Base" ? "#4A9EFF" : "#FF6B6B");
                    const amtV = totalAmt > 0 ? Math.abs(Math.round(totalAmt * sc.expectedReturn / 100)) : 0;
                    return (
                      <div key={sc.scenario} className="rounded-xl p-4 text-center border" style={{ background: `${color}0D`, borderColor: `${color}33` }}>
                        <div className="text-[11px] font-bold uppercase tracking-wider mb-2" style={{ color }}>{sc.emoji} {sc.scenario}</div>
                        <div className="text-2xl font-black font-sans" style={{ color }}>{sc.expectedReturn > 0 ? "+" : ""}{sc.expectedReturn.toFixed(1)}%</div>
                        <div className="text-xs text-slate-500 mt-1">확률 {sc.probability}%</div>
                        {amtV > 0 && <div className="text-xs text-slate-600 mt-0.5">{sc.expectedReturn >= 0 ? "+" : "-"}{fmt(amtV)}</div>}
                        <div className="text-[10px] text-slate-500 mt-2 border-t pt-2" style={{ borderColor: `${color}22` }}>{sc.description}</div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* 코멘트 */}
              {result.recommendations?.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide">💡 분석 코멘트</h3>
                  {result.recommendations.map((r: string, i: number) => (
                    <div key={i} className="text-sm text-slate-300 bg-slate-800/60 border-l-2 border-blue-500 rounded-r-lg px-4 py-2">{r}</div>
                  ))}
                </div>
              )}

              {/* 즐겨찾기 추가 */}
              <FavoriteAdder holdings={holdings} />

              {/* 백테스팅 */}
              <BacktestPanel holdings={holdings} totalAmt={totalAmt} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
