import { useState, useEffect } from "react";
import { TrendingUp, TrendingDown, RefreshCw, ArrowRight, Activity, AlertTriangle } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchWithFallback, MOCK_ANALYSIS, MOCK_NEWS, type NewsItem } from "@/lib/api";
import { Link } from "wouter";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine
} from "recharts";

interface MacroItem { value: number | null; changePct: number; }
interface MacroData  { [key: string]: MacroItem; }

const INDICATORS = [
  { key: "KOSPI",           label: "KOSPI"          },
  { key: "NASDAQ",          label: "NASDAQ"          },
  { key: "S&P 500",         label: "S&P 500"         },
  { key: "USD/KRW",         label: "USD/KRW"         },
  { key: "DXY",             label: "DXY"             },
  { key: "미국 국채 10년물", label: "미국 국채 10년물" },
  { key: "금 (Gold)",       label: "금 (GOLD)"       },
  { key: "WTI 원유",        label: "WTI 원유"        },
] as const;


// ── 레버리지 시뮬레이터 컴포넌트 ─────────────────────────
function LeverageSimulator() {
  const CHANGE = 10;   // 등락률 %
  const ROUNDS = 5;    // 반복 횟수 (5회)
  const START  = 100;  // 시작 기준값

  // 10회 등락 과정 계산
  const steps = (() => {
    const normal: { up: number; down: number }[] = [];
    const lev2:   { up: number; down: number }[] = [];
    let n = START, l = START;
    for (let i = 0; i < ROUNDS; i++) {
      const nUp  = n * (1 + CHANGE / 100);
      const nDn  = nUp * (1 - CHANGE / 100);
      const lUp  = l * (1 + (CHANGE * 2) / 100);
      const lDn  = lUp * (1 - (CHANGE * 2) / 100);
      normal.push({ up: nUp, down: nDn });
      lev2.push({ up: lUp, down: lDn });
      n = nDn;
      l = lDn;
    }
    return { normal, lev2 };
  })();

  const BAR_W = 36;
  const BAR_GAP = 6;
  const PAIR_GAP = 20;
  const CHART_H = 240;
  const LABEL_H = 48;
  const SVG_H = CHART_H + LABEL_H + 20;
  const PADDING_L = 44;
  const totalPairs = ROUNDS;
  const pairW = BAR_W * 2 + BAR_GAP + PAIR_GAP;
  const SVG_W = PADDING_L + totalPairs * pairW + 40;

  // Y축 스케일
  const allVals = [
    START,
    ...steps.normal.flatMap(s => [s.up, s.down]),
    ...steps.lev2.flatMap(s => [s.up, s.down]),
  ];
  const yMin = Math.min(...allVals) - 5;
  const yMax = Math.max(...allVals) + 5;
  const toY = (v: number) => LABEL_H + CHART_H - ((v - yMin) / (yMax - yMin)) * CHART_H;
  const baseY = toY(START);

  const renderChart = (data: { up: number; down: number }[], color: string, title: string) => (
    <div className="flex-1 min-w-0">
      <div className="text-xs font-bold text-center mb-2" style={{ color }}>{title}</div>
      <svg width="100%" viewBox={`0 0 ${SVG_W} ${SVG_H}`} className="overflow-visible w-full">
        {/* 기준선 */}
        <line x1={PADDING_L} y1={baseY} x2={SVG_W} y2={baseY}
          stroke="#475569" strokeWidth="1" strokeDasharray="4 2" />
        <text x={PADDING_L - 4} y={baseY + 4} textAnchor="end" fontSize="9" fill="#64748B">100</text>

        {/* Y축 눈금 */}
        {[Math.floor(yMin/5)*5, Math.ceil((yMax)/5)*5].map(v => (
          <g key={v}>
            <line x1={PADDING_L} y1={toY(v)} x2={SVG_W} y2={toY(v)}
              stroke="#1E2433" strokeWidth="0.5" />
            <text x={PADDING_L - 4} y={toY(v) + 4} textAnchor="end" fontSize="9" fill="#334155">
              {v.toFixed(0)}
            </text>
          </g>
        ))}

        {/* 시작 바 */}
        <rect x={PADDING_L} y={toY(START)} width={BAR_W} height={Math.abs(toY(START) - toY(START)) || 3}
          fill="#94A3B8" rx="2" />
        <text x={PADDING_L + BAR_W/2} y={toY(START) - 4} textAnchor="middle" fontSize="8" fill="#94A3B8">시작</text>

        {/* 등락 바 */}
        {data.map((s, i) => {
          const x = PADDING_L + BAR_W + PAIR_GAP/2 + i * pairW;
          const upH   = Math.abs(toY(s.up)   - baseY);
          const downH = Math.abs(toY(s.down) - baseY);
          const upY   = s.up   >= START ? toY(s.up)   : baseY;
          const downY = s.down >= START ? baseY        : toY(s.down);
          return (
            <g key={i}>
              {/* 상승 바 (초록) */}
              <rect x={x} y={upY} width={BAR_W} height={Math.max(upH, 2)}
                fill={s.up >= START ? "#10B981" : "#EF4444"} rx="2" opacity="0.9" />
              <text x={x + BAR_W/2} y={upY - 3} textAnchor="middle" fontSize="8.5"
                fill={s.up >= START ? "#6EE7B7" : "#FCA5A5"}>
                {s.up.toFixed(1)}
              </text>
              <text x={x + BAR_W/2} y={upY + Math.max(upH,2) + 8} textAnchor="middle" fontSize="8"
                fill={s.up >= START ? "#6EE7B7" : "#FCA5A5"}>
                ({s.up >= START ? "+" : ""}{((s.up - START) / START * 100).toFixed(1)}%)
              </text>

              {/* 하락 바 (빨강) */}
              <rect x={x + BAR_W + BAR_GAP} y={downY} width={BAR_W} height={Math.max(downH, 2)}
                fill="#EF4444" rx="2" opacity="0.9" />
              <text x={x + BAR_W + BAR_GAP + BAR_W/2} y={downY + Math.max(downH,2) + 8}
                textAnchor="middle" fontSize="8.5" fill="#FCA5A5">
                {s.down.toFixed(1)}
              </text>
              <text x={x + BAR_W + BAR_GAP + BAR_W/2} y={downY + Math.max(downH,2) + 17}
                textAnchor="middle" fontSize="8" fill="#FCA5A5">
                ({((s.down - START) / START * 100).toFixed(1)}%)
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );

  const finalNormal = steps.normal[ROUNDS-1].down;
  const finalLev2   = steps.lev2[ROUNDS-1].down;

  return (
    <div className="bg-card border border-border rounded-xl p-5">
      <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1">
        ⚡ 레버리지 투자 — 변동성 손실 시뮬레이션
      </h3>
      <p className="text-xs text-slate-500 mb-4">
        하루 +{CHANGE}%, 다음날 -{CHANGE}%를 번갈아 {ROUNDS}회 반복하면 어떻게 될까요?
        (시작값 100 기준)
      </p>

      <div className="grid grid-cols-2 gap-4">
        {renderChart(steps.normal, "#10B981", `일반 주식 (±${CHANGE}%)`)}
        {renderChart(steps.lev2,   "#F59E0B", `2배 레버리지 (±${CHANGE*2}%)`)}
      </div>

      {/* 최종 결과 비교 */}
      <div className="grid grid-cols-2 gap-3 mt-4">
        <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-3 text-center">
          <div className="text-xs text-slate-400 mb-1">일반 주식 최종</div>
          <div className={`text-xl font-bold font-mono ${finalNormal >= START ? "text-emerald-400" : "text-rose-400"}`}>
            {finalNormal.toFixed(2)}
          </div>
          <div className="text-xs text-slate-500">
            100만원 → {(10000 * finalNormal).toLocaleString()}원
            ({finalNormal >= START ? "+" : ""}{(finalNormal - START).toFixed(2)}%)
          </div>
        </div>
        <div className="bg-slate-800/60 border border-amber-500/20 rounded-xl p-3 text-center">
          <div className="text-xs text-amber-400 mb-1 font-semibold">2배 레버리지 최종</div>
          <div className={`text-xl font-bold font-mono ${finalLev2 >= START ? "text-emerald-400" : "text-rose-400"}`}>
            {finalLev2.toFixed(2)}
          </div>
          <div className="text-xs text-slate-500">
            100만원 → {(10000 * finalLev2).toLocaleString()}원
            ({finalLev2 >= START ? "+" : ""}{(finalLev2 - START).toFixed(2)}%)
          </div>
        </div>
      </div>

      <div className="mt-3 text-xs text-amber-400/80 bg-amber-500/10 border border-amber-500/20 rounded-lg px-4 py-2.5 text-center">
        ⚠️ 일반 주식은 원금이 거의 유지되지만, 레버리지는 같은 조건에서 큰 손실이 발생합니다
      </div>
    </div>
  );
}


export default function Dashboard() {
  const [macro,      setMacro]      = useState<MacroData | null>(null);
  const [analysis,   setAnalysis]   = useState<any>(null);
  const [news,       setNews]       = useState<NewsItem[]>(MOCK_NEWS);
  const [loading,    setLoading]    = useState(true);
  const [loadingAdv, setLoadingAdv] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [time,       setTime]       = useState(new Date());

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const load = async () => {
    setRefreshing(true);

    // ① 거시경제 지표를 단독으로 먼저 호출 (서버 동시 연결 제한 회피)
    const mRes = await fetchWithFallback<{ ok: boolean; data: MacroData }>(
      "/macro", {}, { ok: false, data: {} }
    );
    if (mRes.ok) setMacro(mRes.data);
    setLoading(false);

    // ② 뉴스 로드
    const nRes = await fetchWithFallback<any>("/news/market?limit=4", {}, MOCK_NEWS);
    const newsData = Array.isArray(nRes) ? nRes : (nRes?.data || MOCK_NEWS);
    setNews(newsData);

    // ③ 심화 분석 로드
    const aRes = await fetchWithFallback<{ ok: boolean; data: any }>(
      "/macro/analysis", {}, { ok: false, data: null }
    );
    if (aRes.ok && aRes.data) setAnalysis(aRes.data);
    setLoadingAdv(false);
    setRefreshing(false);
  };

  useEffect(() => { load(); }, []);

  const fmtPrice = (v: number | null) => {
    if (v === null || v === undefined) return "—";
    return v >= 1000 ? v.toLocaleString("ko-KR", { maximumFractionDigits: 2 }) : v.toFixed(2);
  };

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500 font-mono">
          {time.toLocaleDateString("ko-KR", { weekday:"long", year:"numeric", month:"long", day:"numeric" })}
          {" · "}{time.toLocaleTimeString("ko-KR")}
        </p>
        <button onClick={load}
          className="flex items-center gap-2 text-xs text-slate-400 hover:text-slate-200 transition-colors px-3 py-1.5 rounded-lg border border-slate-700 hover:border-slate-500">
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
          새로고침
        </button>
      </div>

      {/* ① 거시경제 지표 */}
      <section>
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">주요 거시경제 지표</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {INDICATORS.map(({ key, label }) => {
            const d = macro?.[key];
            const up = d ? d.changePct >= 0 : true;
            return (
              <div key={key} className="bg-card border border-border rounded-xl p-4 hover:border-slate-600 transition-colors">
                <div className="text-[11px] text-slate-500 mb-2 uppercase tracking-wide">{label}</div>
                {loading || !macro ? (
                  <><Skeleton className="h-6 w-24 mb-1 bg-slate-800" /><Skeleton className="h-4 w-16 bg-slate-800" /></>
                ) : !d || d.value === null ? (
                  <><div className="text-lg font-bold font-mono text-slate-500">—</div><div className="text-xs text-slate-600 mt-1">데이터 없음</div></>
                ) : (
                  <>
                    <div className="text-lg font-bold font-mono text-white leading-tight">{fmtPrice(d.value)}</div>
                    <div className={`flex items-center gap-1 mt-1 text-xs font-mono font-semibold ${up ? "text-emerald-400" : "text-rose-400"}`}>
                      {up ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                      {up ? "+" : ""}{d.changePct?.toFixed(2)}%
                    </div>
                  </>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* ② 코스피 달러 환산 + 반도체 쏠림 */}
      <section>
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          지수 쏠림 분석 & 실질 가치 평가
        </h2>

        {loadingAdv ? (
          <div className="grid grid-cols-3 gap-3">
            {Array.from({length:3}).map((_,i) => <Skeleton key={i} className="h-24 bg-slate-800 rounded-xl" />)}
          </div>
        ) : !analysis ? (
          <div className="text-center py-8 text-slate-500 text-sm border border-dashed border-slate-700 rounded-xl">심화 분석 데이터를 불러올 수 없습니다.</div>
        ) : (
          <div className="space-y-6">
            {/* 코스피 달러 환산 */}
            {analysis.kospi_usd && !analysis.kospi_usd.error && (
              <div className="bg-card border border-border rounded-xl p-5">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-4">💵 코스피 달러 환산 실질 가치</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="text-xs text-slate-400 mb-1">코스피 (원화)</div>
                    <div className="text-2xl font-bold font-mono text-white">{analysis.kospi_usd.current_krw?.toLocaleString()} pt</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">USD/KRW</div>
                    <div className="text-2xl font-bold font-mono text-white">{analysis.kospi_usd.usdkrw?.toLocaleString()} 원</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">코스피 (달러 환산)</div>
                    <div className="text-2xl font-bold font-mono text-white">${analysis.kospi_usd.current_usd?.toFixed(2)}</div>
                  </div>
                </div>
                <p className="text-xs text-slate-500 mt-3">💡 {analysis.kospi_usd.description}</p>
              </div>
            )}

            {/* 반도체 쏠림 분석 */}
            {analysis.semiconductor_skew && !analysis.semiconductor_skew.error && (() => {
              const sk = analysis.semiconductor_skew;
              const chartData = [
                { name: "삼성+하이닉스", value: sk.semicon_contribution, fill: "#EF4444" },
                { name: "나머지 종목",   value: sk.others_contribution,  fill: "#4A9EFF" },
              ];
              return (
                <div className="bg-card border border-border rounded-xl p-5">
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-4">📈 코스피 상승 기여도 분해 ({sk.period})</h3>
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div>
                      <div className="text-xs text-slate-400 mb-1">코스피 전체 상승</div>
                      <div className="text-2xl font-bold font-mono text-white">{sk.kospi_return > 0 ? "+" : ""}{sk.kospi_return?.toFixed(2)}%</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">삼성+하이닉스 기여</div>
                      <div className="text-2xl font-bold font-mono text-rose-400">{sk.semicon_contribution > 0 ? "+" : ""}{sk.semicon_contribution?.toFixed(2)}%p</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">나머지 종목 기여</div>
                      <div className="text-2xl font-bold font-mono text-blue-400">{sk.others_contribution > 0 ? "+" : ""}{sk.others_contribution?.toFixed(2)}%p</div>
                    </div>
                  </div>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={chartData} margin={{ top: 20, right: 20, bottom: 5, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#2D3142" />
                      <XAxis dataKey="name" tick={{ fill: "#8891AA", fontSize: 12 }} />
                      <YAxis tick={{ fill: "#8891AA", fontSize: 11 }} />
                      <ReferenceLine y={sk.kospi_return} stroke="#FFFFFF" strokeDasharray="4 4"
                        label={{ value: `코스피 전체 ${sk.kospi_return > 0 ? "+" : ""}${sk.kospi_return?.toFixed(2)}%`, fill: "#FFFFFF", fontSize: 11, position: "right" }} />
                      <Tooltip formatter={(v: any) => `${v > 0 ? "+" : ""}${Number(v).toFixed(2)}%p`}
                        contentStyle={{ background: "#1E2130", border: "1px solid #2D3142", borderRadius: "8px", fontSize: "12px" }} />
                      <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                        {chartData.map((entry, i) => (
                          <rect key={i} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  <div className={`mt-3 text-sm px-4 py-2 rounded-lg border ${sk.semicon_ratio_pct > 60 ? "bg-rose-500/10 border-rose-500/20 text-rose-300" : sk.semicon_ratio_pct > 40 ? "bg-amber-500/10 border-amber-500/20 text-amber-300" : "bg-emerald-500/10 border-emerald-500/20 text-emerald-300"}`}>
                    {sk.semicon_ratio_pct > 60 ? "⚠️" : sk.semicon_ratio_pct > 40 ? "📌" : "✅"}
                    {" "}지수 상승의 <strong>{sk.semicon_ratio_pct?.toFixed(0)}%</strong>가 반도체 2종목에 집중
                  </div>
                </div>
              );
            })()}

            {/* DXY 분석 */}
            {analysis.dxy_analysis && !analysis.dxy_analysis.error && (
              <div className="bg-card border border-border rounded-xl p-5">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-4">💵 달러 인덱스(DXY) 반영 실질 자산가치 분석</h3>
                <div className="grid grid-cols-3 gap-4 mb-3">
                  <div>
                    <div className="text-xs text-slate-400 mb-1">달러 인덱스 (DXY)</div>
                    <div className="text-2xl font-bold font-mono text-white">{analysis.dxy_analysis.dxy_current?.toFixed(2)}</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">DXY 1년 변화</div>
                    <div className={`text-2xl font-bold font-mono ${(analysis.dxy_analysis.dxy_1y_change ?? 0) >= 0 ? "text-rose-400" : "text-emerald-400"}`}>
                      {(analysis.dxy_analysis.dxy_1y_change ?? 0) >= 0 ? "+" : ""}{analysis.dxy_analysis.dxy_1y_change?.toFixed(2)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">코스피-DXY 상관계수</div>
                    <div className="text-2xl font-bold font-mono text-white">{analysis.dxy_analysis.kospi_dxy_corr?.toFixed(3)}</div>
                  </div>
                </div>
                <div className="text-sm text-blue-300 bg-blue-500/10 border border-blue-500/20 rounded-lg px-4 py-2">
                  📊 {analysis.dxy_analysis.interpretation}
                </div>
              </div>
            )}

            {/* 개인 vs 기관 vs 외국인 */}
            {analysis.investor_returns && (
              <div className="bg-card border border-border rounded-xl p-5">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-4">👤 개인 vs 기관 vs 외국인 연간 수익률 비교</h3>
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={analysis.investor_returns.data} margin={{ top: 10, right: 10, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2D3142" />
                    <XAxis dataKey="year" tick={{ fill: "#8891AA", fontSize: 12 }} />
                    <YAxis tick={{ fill: "#8891AA", fontSize: 11 }} tickFormatter={v => `${v}%`} />
                    <ReferenceLine y={0} stroke="#444860" />
                    <Tooltip formatter={(v: any) => `${Number(v).toFixed(1)}%`}
                      contentStyle={{ background: "#1E2130", border: "1px solid #2D3142", borderRadius: "8px", fontSize: "12px" }} />
                    <Bar dataKey="individual"   name="개인"   fill="#EF4444" radius={[3,3,0,0]} />
                    <Bar dataKey="institutional" name="기관"  fill="#4A9EFF" radius={[3,3,0,0]} />
                    <Bar dataKey="foreign"       name="외국인" fill="#21C45D" radius={[3,3,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
                <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-rose-500 inline-block"/>개인</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-blue-500 inline-block"/>기관</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-emerald-500 inline-block"/>외국인</span>
                </div>
                <p className="text-xs text-slate-500 mt-2">📌 {analysis.investor_returns.insight}</p>
              </div>
            )}

            {/* 레버리지 투자 시뮬레이터 */}
            <LeverageSimulator />
          </div>
        )}
      </section>

      {/* ③ 최신 뉴스 */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">최신 시장 뉴스</h2>
          <Link href="/news">
            <span className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors cursor-pointer">
              전체 보기 <ArrowRight className="w-3 h-3" />
            </span>
          </Link>
        </div>
        <div className="bg-card border border-border rounded-xl overflow-hidden divide-y divide-border">
          {loading
            ? Array.from({length:4}).map((_,i) => (
                <div key={i} className="p-4 flex items-center gap-4">
                  <Skeleton className="w-10 h-10 rounded-lg bg-slate-800 shrink-0" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-full bg-slate-800" />
                    <Skeleton className="h-3 w-32 bg-slate-800" />
                  </div>
                </div>
              ))
            : news.slice(0,4).map((item, i) => {
                const rawScore = (item as any).sentimentScore ?? (item as any).sentiment_score ?? 0;
                const pos = rawScore > 0;
                return (
                  <a key={i} href={(item.url !== "#" ? item.url : undefined)} target="_blank" rel="noreferrer"
                    className="p-4 hover:bg-slate-800/40 transition-colors flex items-start gap-3 block">
                    <div className={`shrink-0 w-10 h-10 rounded-lg flex items-center justify-center font-mono text-sm font-bold border
                      ${pos ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border-rose-500/20"}`}>
                      {pos ? "+" : ""}{rawScore.toFixed(1)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-200 font-medium line-clamp-1">{item.title}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-slate-500">{item.source || ""}</span>
                        <span className="text-xs text-slate-600">{(item as any).date || item.published || ""}</span>
                        {(item as any).grade && (
                          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded text-white
                            ${(item as any).grade==="A"?"bg-emerald-600":(item as any).grade==="B"?"bg-blue-600":(item as any).grade==="C"?"bg-amber-600":"bg-rose-600"}`}>
                            {(item as any).grade}
                          </span>
                        )}
                      </div>
                    </div>
                  </a>
                );
              })}
        </div>
      </section>
    </div>
  );
}
