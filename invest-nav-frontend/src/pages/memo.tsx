import { useState, useEffect } from "react";
import { Plus, Trash2, Save, Edit3, X, ChevronDown, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { fetchWithFallback, postJSON, MOCK_MEMOS } from "@/lib/api";

interface Memo {
  id: number; title: string; content: string;
  stock: string; tags: string[]; created_at: string; updated_at: string;
}

const SECTIONS = [
  { id: "investment_thesis",    title: "1️⃣ 투자 논거",          placeholder: "이 주식에 투자하는 핵심 이유를 3가지 이내로 작성하세요.", tip: "좋은 투자 논거는 1~2문장으로 요약 가능해야 합니다." },
  { id: "business_overview",    title: "2️⃣ 사업 개요",          placeholder: "사업 모델, 주요 제품/서비스, 수익 구조를 설명하세요.", tip: "DART 사업보고서의 '사업의 내용' 섹션을 참고하세요." },
  { id: "financial_analysis",   title: "3️⃣ 재무 분석",          placeholder: "최근 3~5년 재무 트렌드를 분석하세요.", tip: "매출 성장률, 영업이익률, ROE 변화를 중점적으로 분석하세요." },
  { id: "competitive_advantage",title: "4️⃣ 경쟁 우위 (Moat)",   placeholder: "모트(Moat)를 분석하세요.", tip: "워런 버핏의 '해자(Moat)': 10년 후에도 유지될 경쟁 우위인가?" },
  { id: "risk_analysis",        title: "5️⃣ 리스크 분석",        placeholder: "주요 리스크를 솔직하게 작성하세요.", tip: "리스크를 직시하지 않는 투자자는 리스크에 당합니다!" },
  { id: "valuation",            title: "6️⃣ 밸류에이션",         placeholder: "현재 적정가 산정 근거를 작성하세요.", tip: "여러 방법론(PER, PBR, DCF)을 사용해 교차 검증하세요." },
  { id: "catalyst",             title: "7️⃣ 촉매제 (Catalyst)",  placeholder: "주가 상승을 이끌 구체적인 이벤트와 시기를 작성하세요.", tip: "촉매가 없는 주식은 언제 오를지 알 수 없습니다." },
  { id: "variant_view",         title: "8️⃣ Variant View",       placeholder: "시장 컨센서스와 다른 나의 관점을 작성하세요.", tip: "Variant View = 내가 시장보다 아는 것." },
  { id: "rr_score_memo",        title: "9️⃣ R/R 점수 평가",      placeholder: "이 투자의 위험/보상 비율을 평가하세요.\nR/R Score: __/10", tip: "R/R ≥ 3:1 (Score ≥ 7)이 아니면 포지션 크기를 줄이세요." },
  { id: "conclusion",           title: "🔟 결론 & 액션 플랜",    placeholder: "최종 투자 결론과 구체적인 액션을 작성하세요.", tip: "메모는 쓰는 것이 아니라 실행하는 것입니다!" },
];

function formatDate(s: string) {
  try { return new Intl.DateTimeFormat("ko-KR", { month: "short", day: "numeric" }).format(new Date(s)); }
  catch { return s; }
}

export default function MemoPage() {
  const [memos, setMemos]       = useState<Memo[]>([]);
  const [current, setCurrent]   = useState<Memo | null>(null);
  const [editing, setEditing]   = useState(false);
  const [form, setForm]         = useState({ title: "", stock: "", tags: "" });
  const [sections, setSections] = useState<Record<string, string>>({});
  const [expanded, setExpanded] = useState<string | null>("investment_thesis");
  const [saving, setSaving]     = useState(false);
  const [tagInput, setTagInput] = useState("");

  useEffect(() => {
    fetchWithFallback<Memo[]>("/memo", {}, MOCK_MEMOS).then(data => {
      setMemos(Array.isArray(data) ? data : MOCK_MEMOS);
    });
  }, []);

  const newMemo = () => {
    setCurrent(null);
    setForm({ title: "", stock: "", tags: "" });
    setSections({});
    setEditing(true);
    setExpanded("investment_thesis");
  };

  const openMemo = (m: Memo) => {
    setCurrent(m);
    setForm({ title: m.title, stock: m.stock, tags: m.tags.join(", ") });
    try { setSections(JSON.parse(m.content)); } catch { setSections({ conclusion: m.content }); }
    setEditing(false);
  };

  const save = async () => {
    if (!form.title.trim()) return;
    setSaving(true);
    const payload = {
      title: form.title, stock: form.stock,
      content: JSON.stringify(sections),
      tags: form.tags.split(",").map(t => t.trim()).filter(Boolean),
    };
    if (current) {
      const res = await fetchWithFallback<Memo>(`/memo/${current.id}`, { method: "PUT", body: JSON.stringify(payload) }, current);
      setMemos(prev => prev.map(m => m.id === current.id ? res : m));
      setCurrent(res);
    } else {
      const res = await postJSON<Memo>("/memo", payload, { ...payload, id: Date.now(), created_at: new Date().toISOString(), updated_at: new Date().toISOString() });
      setMemos(prev => [res, ...prev]);
      setCurrent(res);
    }
    setEditing(false);
    setSaving(false);
  };

  const deleteMemo = async (id: number) => {
    await fetchWithFallback(`/memo/${id}`, { method: "DELETE" }, {});
    setMemos(prev => prev.filter(m => m.id !== id));
    if (current?.id === id) { setCurrent(null); setEditing(false); }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">투자 메모</h2>
        <p className="text-sm text-slate-500 mt-1">10개 섹션으로 체계적인 투자 분석을 기록하세요.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 메모 목록 */}
        <div className="space-y-3">
          <Button onClick={newMemo} className="w-full bg-blue-600 hover:bg-blue-500" size="sm">
            <Plus className="w-4 h-4 mr-1" /> 새 메모 작성
          </Button>
          <div className="space-y-2">
            {memos.length === 0 ? (
              <div className="text-center py-8 text-slate-500 text-sm border border-dashed border-slate-700 rounded-xl">메모가 없습니다</div>
            ) : memos.map(m => (
              <button key={m.id} onClick={() => openMemo(m)}
                className={`w-full text-left p-3 rounded-xl border transition-colors ${
                  current?.id === m.id ? "bg-blue-600/10 border-blue-500/30" : "bg-card border-border hover:border-slate-600"
                }`}>
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-medium text-white truncate">{m.title}</p>
                  <button onClick={e => { e.stopPropagation(); deleteMemo(m.id); }}
                    className="text-slate-600 hover:text-rose-400 transition-colors shrink-0">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
                {m.stock && <p className="text-xs text-slate-500 mt-0.5">{m.stock}</p>}
                <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                  {m.tags.slice(0, 3).map(t => (
                    <span key={t} className="text-[10px] bg-slate-800 border border-slate-700 text-slate-400 rounded px-1.5 py-0.5">{t}</span>
                  ))}
                  <span className="text-[10px] text-slate-600 ml-auto">{formatDate(m.updated_at)}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* 메모 편집/보기 */}
        <div className="lg:col-span-2">
          {!current && !editing ? (
            <div className="h-full min-h-64 flex items-center justify-center border border-dashed border-slate-700 rounded-xl">
              <div className="text-center">
                <div className="text-4xl mb-3">📝</div>
                <p className="text-slate-400 font-medium">메모를 선택하거나 새로 작성하세요</p>
              </div>
            </div>
          ) : (
            <div className="bg-card border border-border rounded-xl p-5 space-y-4">
              {/* 헤더 */}
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-300">
                  {editing ? (current ? "메모 편집" : "새 메모") : current?.title}
                </h3>
                <div className="flex items-center gap-2">
                  {!editing && (
                    <button onClick={() => setEditing(true)} className="text-slate-400 hover:text-slate-200 transition-colors">
                      <Edit3 className="w-4 h-4" />
                    </button>
                  )}
                  {editing && (
                    <>
                      <Button onClick={save} disabled={saving} size="sm" className="bg-blue-600 hover:bg-blue-500 text-xs">
                        <Save className="w-3.5 h-3.5 mr-1" />{saving ? "저장 중..." : "저장"}
                      </Button>
                      <button onClick={() => setEditing(false)} className="text-slate-500 hover:text-slate-300 transition-colors">
                        <X className="w-4 h-4" />
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* 기본 정보 */}
              {editing ? (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-slate-400 mb-1 block">제목 *</label>
                    <Input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
                      placeholder="예: 삼성전자 2024년 투자 분석"
                      className="bg-slate-800 border-slate-700 text-slate-200 placeholder:text-slate-500 text-sm h-9" />
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 mb-1 block">종목</label>
                    <Input value={form.stock} onChange={e => setForm(f => ({ ...f, stock: e.target.value }))}
                      placeholder="예: 005930.KS"
                      className="bg-slate-800 border-slate-700 text-slate-200 placeholder:text-slate-500 text-sm h-9" />
                  </div>
                  <div className="col-span-2">
                    <label className="text-xs text-slate-400 mb-1 block">태그 (쉼표로 구분)</label>
                    <Input value={form.tags} onChange={e => setForm(f => ({ ...f, tags: e.target.value }))}
                      placeholder="예: 반도체, HBM, 수출"
                      className="bg-slate-800 border-slate-700 text-slate-200 placeholder:text-slate-500 text-sm h-9" />
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3 flex-wrap">
                  {current?.stock && <Badge variant="outline" className="text-blue-400 border-blue-500/30">{current.stock}</Badge>}
                  {current?.tags.map(t => <Badge key={t} variant="outline" className="text-slate-400 border-slate-700">{t}</Badge>)}
                </div>
              )}

              {/* 섹션들 */}
              <div className="space-y-2">
                {SECTIONS.map(sec => {
                  const isOpen = expanded === sec.id;
                  const content = sections[sec.id] || "";
                  return (
                    <div key={sec.id} className="border border-slate-700 rounded-lg overflow-hidden">
                      <button onClick={() => setExpanded(isOpen ? null : sec.id)}
                        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-800/40 transition-colors">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-slate-200">{sec.title}</span>
                          {content && !editing && <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />}
                        </div>
                        {isOpen ? <ChevronDown className="w-4 h-4 text-slate-500" /> : <ChevronRight className="w-4 h-4 text-slate-500" />}
                      </button>
                      {isOpen && (
                        <div className="px-4 pb-4 border-t border-slate-800">
                          <p className="text-[11px] text-blue-400 mt-2 mb-2 flex items-center gap-1">💡 {sec.tip}</p>
                          {editing ? (
                            <Textarea value={content}
                              onChange={e => setSections(prev => ({ ...prev, [sec.id]: e.target.value }))}
                              placeholder={sec.placeholder} rows={4}
                              className="bg-slate-900 border-slate-700 text-slate-200 placeholder:text-slate-600 text-sm resize-none focus-visible:ring-blue-500" />
                          ) : (
                            content ? (
                              <p className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">{content}</p>
                            ) : (
                              <p className="text-sm text-slate-600 italic">{sec.placeholder.split("\n")[0]}</p>
                            )
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
