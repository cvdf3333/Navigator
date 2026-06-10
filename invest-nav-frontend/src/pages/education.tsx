import { useState, useEffect } from "react";
import { Search, ChevronDown, ChevronRight, Lightbulb, BookOpen } from "lucide-react";
import { Input } from "@/components/ui/input";
import { GLOSSARY } from "@/lib/glossary";

export default function Education() {
  const [selectedCat, setSelectedCat] = useState(Object.keys(GLOSSARY)[0]);
  const [searchQ, setSearchQ]         = useState(() => {
    // 검색 모달에서 넘어온 검색어 확인
    const q = sessionStorage.getItem("edu_search") || "";
    sessionStorage.removeItem("edu_search");
    return q;
  });
  const [expanded, setExpanded]       = useState<string | null>(null);

  // 검색어가 있으면 해당 용어 자동 펼치기
  useEffect(() => {
    if (searchQ) {
      const allTerms = Object.values(GLOSSARY).flatMap(cat => Object.keys(cat));
      const match = allTerms.find(t => t.toLowerCase().includes(searchQ.toLowerCase()));
      if (match) setExpanded(match);
    }
  }, []);

  const cats = Object.keys(GLOSSARY);

  let terms = GLOSSARY[selectedCat] || {};
  if (searchQ) {
    const q = searchQ.toLowerCase();
    const allTerms: typeof terms = {};
    for (const cat of cats) {
      for (const [k, v] of Object.entries(GLOSSARY[cat])) {
        if (k.toLowerCase().includes(q) || v["설명"]?.toLowerCase().includes(q)) {
          allTerms[k] = v;
        }
      }
    }
    terms = allTerms;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">금융 백과사전</h2>
        <p className="text-sm text-slate-500 mt-1">투자에 꼭 필요한 금융 용어와 개념을 쉽게 설명합니다.</p>
      </div>

      {/* 검색 */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <Input value={searchQ} onChange={e => setSearchQ(e.target.value)}
          placeholder="용어 검색 (PER, 배당, 분산...)"
          className="pl-9 bg-slate-800 border-slate-700 text-slate-200 placeholder:text-slate-500 focus-visible:ring-blue-500" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* 카테고리 사이드바 */}
        {!searchQ && (
          <div className="space-y-1">
            {cats.map(cat => (
              <button key={cat} onClick={() => setSelectedCat(cat)}
                className={`w-full text-left px-4 py-2.5 rounded-lg text-sm transition-colors ${
                  selectedCat === cat
                    ? "bg-blue-600/15 text-blue-400 border border-blue-500/20 font-medium"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent"
                }`}>
                {cat}
                <span className="ml-2 text-xs opacity-60">({Object.keys(GLOSSARY[cat]).length})</span>
              </button>
            ))}
          </div>
        )}

        {/* 용어 목록 */}
        <div className={`space-y-2 ${!searchQ ? "lg:col-span-3" : "lg:col-span-4"}`}>
          {searchQ && (
            <p className="text-xs text-slate-500 mb-3">
              검색 결과: <span className="text-slate-300 font-medium">{Object.keys(terms).length}개</span>
            </p>
          )}
          {Object.keys(terms).length === 0 ? (
            <div className="text-center py-12 text-slate-500">검색 결과가 없습니다.</div>
          ) : (
            Object.entries(terms).map(([termName, item]) => {
              const isOpen = expanded === termName;
              return (
                <div key={termName} className="bg-card border border-border rounded-xl overflow-hidden">
                  <button onClick={() => setExpanded(isOpen ? null : termName)}
                    className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-slate-800/40 transition-colors">
                    <div className="flex items-center gap-3">
                      <BookOpen className="w-4 h-4 text-blue-400 shrink-0" />
                      <span className="text-sm font-semibold text-white">{termName}</span>
                    </div>
                    {isOpen ? <ChevronDown className="w-4 h-4 text-slate-500" /> : <ChevronRight className="w-4 h-4 text-slate-500" />}
                  </button>
                  {isOpen && (
                    <div className="px-5 pb-5 space-y-3 border-t border-border">
                      {item["설명"] && (
                        <div className="pt-4">
                          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wide">📖 정의</div>
                          <p className="text-sm text-slate-200 leading-relaxed">{item["설명"]}</p>
                        </div>
                      )}
                      {item["예시"] && (
                        <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg px-4 py-3">
                          <div className="text-xs text-blue-400 mb-1">📝 예시</div>
                          <p className="text-sm text-slate-300">{item["예시"]}</p>
                        </div>
                      )}
                      {item["핵심"] && (
                        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-4 py-3 flex gap-3">
                          <Lightbulb className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                          <p className="text-sm text-slate-300">{item["핵심"]}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
