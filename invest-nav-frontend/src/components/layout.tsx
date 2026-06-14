import { Link, useLocation } from "wouter";
import {
  LayoutDashboard, Briefcase, Newspaper, BookOpen,
  Star, Bell, Search, X, TrendingUp, TrendingDown,
  Plus, Trash2, ChevronRight, Loader2
} from "lucide-react";
import { useState, useEffect, useRef } from "react";
import { GLOSSARY } from "@/lib/glossary";
import { getFavorites, addFavorite, removeFavorite, isFavorite, type FavoriteStock } from "@/lib/favorites";
import { getAuth, setAuth, clearAuth, setNickname, login, register, updateNickname, fetchServerFavorites, syncFavorites, type AuthUser } from "@/lib/auth";
import { fetchWithFallback } from "@/lib/api";
import { POPULAR_STOCKS } from "@/lib/stocks";

const NAV_ITEMS = [
  { icon: LayoutDashboard, label: "대시보드",    href: "/"          },
  { icon: Briefcase,       label: "포트폴리오",  href: "/portfolio" },
  { icon: Newspaper,       label: "뉴스 & 공시", href: "/news"      },
  { icon: BookOpen,        label: "금융 백과사전",href: "/education" },
];

// ── 검색 모달 (돋보기) ────────────────────────────────────
function SearchModal({ onClose }: { onClose: () => void }) {
  const [q, setQ]           = useState("");
  const [, navigate]        = useLocation();
  const inputRef            = useRef<HTMLInputElement>(null);

  useEffect(() => { inputRef.current?.focus(); }, []);

  // 금융 백과사전에서 검색
  const results: { term: string; category: string; desc: string }[] = [];
  if (q.trim().length >= 1) {
    for (const [cat, terms] of Object.entries(GLOSSARY)) {
      for (const [term, data] of Object.entries(terms)) {
        if (
          term.toLowerCase().includes(q.toLowerCase()) ||
          (data as any)["설명"]?.toLowerCase().includes(q.toLowerCase())
        ) {
          results.push({ term, category: cat, desc: (data as any)["설명"] || "" });
          if (results.length >= 8) break;
        }
      }
      if (results.length >= 8) break;
    }
  }

  const goToTerm = (term: string) => {
    // education 페이지로 이동 + 검색어 state 전달
    sessionStorage.setItem("edu_search", term);
    navigate("/education");
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-start justify-center pt-24"
      onClick={onClose}>
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-xl mx-4 shadow-2xl overflow-hidden"
        onClick={e => e.stopPropagation()}>
        {/* 검색 입력 */}
        <div className="flex items-center gap-3 px-5 py-4 border-b border-slate-800">
          <Search className="w-5 h-5 text-slate-400 shrink-0" />
          <input ref={inputRef} value={q} onChange={e => setQ(e.target.value)}
            placeholder="금융 용어 검색... (예: PER, 배당, 분산투자)"
            className="flex-1 bg-transparent text-slate-200 placeholder:text-slate-500 outline-none text-base" />
          {q && <button onClick={() => setQ("")}><X className="w-4 h-4 text-slate-500" /></button>}
        </div>

        {/* 결과 */}
        <div className="max-h-80 overflow-y-auto">
          {q.trim() === "" ? (
            <div className="px-5 py-8 text-center text-slate-500 text-sm">
              금융 용어를 입력하면 백과사전에서 찾아드려요
            </div>
          ) : results.length === 0 ? (
            <div className="px-5 py-8 text-center text-slate-500 text-sm">
              '{q}'에 대한 검색 결과가 없어요
            </div>
          ) : results.map((r, i) => (
            <button key={i} onClick={() => goToTerm(r.term)}
              className="w-full flex items-start gap-4 px-5 py-3.5 hover:bg-slate-800 transition-colors text-left border-b border-slate-800/50 last:border-0">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-sm font-semibold text-white">{r.term}</span>
                  <span className="text-[10px] bg-blue-500/20 text-blue-400 border border-blue-500/30 px-1.5 py-0.5 rounded">
                    {r.category}
                  </span>
                </div>
                <p className="text-xs text-slate-400 line-clamp-1">{r.desc}</p>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-600 shrink-0 mt-1" />
            </button>
          ))}
        </div>

        {results.length > 0 && (
          <div className="px-5 py-3 border-t border-slate-800 text-xs text-slate-500 text-center">
            클릭하면 금융 백과사전으로 이동해요
          </div>
        )}
      </div>
    </div>
  );
}

// ── 알림 패널 (즐겨찾기 뉴스) ─────────────────────────────
function NotificationPanel({ onClose }: { onClose: () => void }) {
  const [favs, setFavs]           = useState<FavoriteStock[]>([]);
  const [newsMap, setNewsMap]     = useState<Record<string, any>>({});
  const [loading, setLoading]     = useState<Record<string, boolean>>({});

  useEffect(() => {
    const f = getFavorites();
    setFavs(f);
    // 각 즐겨찾기 종목 뉴스 요약 로드
    f.forEach(async (fav) => {
      setLoading(prev => ({ ...prev, [fav.symbol]: true }));
      const res = await fetchWithFallback<any>(
        `/news/${encodeURIComponent(fav.symbol)}?limit=5`, {}, null
      );
      if (res?.ok && res.data) {
        const news = res.data;
        const pos = news.filter((n: any) => (n.sentimentLabel ?? n.sentiment_label) === "positive").length;
        const neg = news.filter((n: any) => (n.sentimentLabel ?? n.sentiment_label) === "negative").length;
        const avg = news.length > 0
          ? news.reduce((s: number, n: any) => s + (n.sentimentScore ?? n.sentiment_score ?? 0), 0) / news.length
          : 0;
        setNewsMap(prev => ({ ...prev, [fav.symbol]: { pos, neg, avg: avg.toFixed(2), total: news.length } }));
      }
      setLoading(prev => ({ ...prev, [fav.symbol]: false }));
    });
  }, []);

  const remove = (symbol: string) => {
    removeFavorite(symbol);
    setFavs(getFavorites());
  };

  return (
    <div className="absolute right-0 top-10 w-80 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-50 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <span className="text-sm font-semibold text-white flex items-center gap-2">
          <Star className="w-4 h-4 text-amber-400" /> 즐겨찾기 뉴스
        </span>
        <button onClick={onClose}><X className="w-4 h-4 text-slate-500" /></button>
      </div>

      <div className="max-h-96 overflow-y-auto">
        {favs.length === 0 ? (
          <div className="px-4 py-8 text-center text-slate-500 text-sm">
            즐겨찾기 종목이 없어요<br />
            <span className="text-xs mt-1 block">프로필 또는 포트폴리오에서 추가하세요</span>
          </div>
        ) : favs.map(fav => {
          const news = newsMap[fav.symbol];
          const isLoading = loading[fav.symbol];
          const avg = news ? parseFloat(news.avg) : 0;
          return (
            <div key={fav.symbol} className="px-4 py-3 border-b border-slate-800/50 last:border-0">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <span className="text-sm font-medium text-white">{fav.name}</span>
                  <span className="text-xs text-slate-500 ml-2 font-mono">{fav.symbol}</span>
                </div>
                <button onClick={() => remove(fav.symbol)}
                  className="text-slate-600 hover:text-rose-400 transition-colors">
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
              {isLoading ? (
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <Loader2 className="w-3 h-3 animate-spin" /> 뉴스 불러오는 중...
                </div>
              ) : news ? (
                <div className="flex items-center gap-3 text-xs">
                  <span className={`font-bold font-mono ${avg >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {avg >= 0 ? "+" : ""}{news.avg}
                  </span>
                  <span className="text-emerald-400 flex items-center gap-1">
                    <TrendingUp className="w-3 h-3" /> {news.pos}건
                  </span>
                  <span className="text-rose-400 flex items-center gap-1">
                    <TrendingDown className="w-3 h-3" /> {news.neg}건
                  </span>
                  <span className="text-slate-500">총 {news.total}건</span>
                </div>
              ) : (
                <span className="text-xs text-slate-600">뉴스 데이터 없음</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── 프로필 패널 (즐겨찾기 관리) ───────────────────────────
function ProfilePanel({ onClose }: { onClose: () => void }) {
  const [favs, setFavs]   = useState<FavoriteStock[]>(getFavorites());
  const [searchQ, setSearchQ] = useState("");
  const [showAdd, setShowAdd] = useState(false);

  const filtered = searchQ.trim()
    ? POPULAR_STOCKS.filter(s =>
        s.name.toLowerCase().includes(searchQ.toLowerCase()) ||
        s.symbol.toLowerCase().includes(searchQ.toLowerCase())
      ).slice(0, 6)
    : [];

  const add = (s: typeof POPULAR_STOCKS[number]) => {
    addFavorite({ symbol: s.symbol, name: s.name, market: s.market });
    setFavs(getFavorites());
    setSearchQ("");
    setShowAdd(false);
  };

  const remove = (symbol: string) => {
    removeFavorite(symbol);
    setFavs(getFavorites());
  };

  const auth = getAuth();
  const displayName = auth?.nickname || "게스트";
  const initial = displayName.charAt(0);

  const [editingNick, setEditingNick] = useState(false);
  const [nickInput, setNickInput]     = useState(displayName);
  const [nickError, setNickError]     = useState("");

  const handleLogout = () => {
    clearAuth();
    window.location.reload();
  };

  const saveNickname = async () => {
    const trimmed = nickInput.trim();
    if (!trimmed) { setNickError("닉네임을 입력해주세요"); return; }
    if (trimmed.length > 12) { setNickError("12자 이하로 입력해주세요"); return; }

    const res = await updateNickname(trimmed);
    if (res?.ok) {
      setNickname(trimmed);
      setEditingNick(false);
      setNickError("");
      window.location.reload();
    } else {
      setNickError(res?.error || "변경 실패");
    }
  };

  return (
    <div className="absolute left-0 bottom-14 w-96 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-50 overflow-hidden">
      {/* 프로필 헤더 */}
      <div className="px-4 py-4 border-b border-slate-800 bg-gradient-to-r from-blue-600/20 to-purple-600/20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold">{initial}</div>
          <div className="flex-1 min-w-0">
            {editingNick ? (
              <div className="space-y-1">
                <input value={nickInput} onChange={e => setNickInput(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && saveNickname()}
                  maxLength={12} autoFocus
                  className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm text-white outline-none focus:border-blue-500" />
                {nickError && <p className="text-[10px] text-rose-400">{nickError}</p>}
                <div className="flex gap-1">
                  <button onClick={saveNickname} className="text-[10px] text-blue-400 hover:text-blue-300">저장</button>
                  <button onClick={() => { setEditingNick(false); setNickInput(displayName); setNickError(""); }} className="text-[10px] text-slate-500 hover:text-slate-400">취소</button>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-1.5">
                <div className="text-sm font-bold text-white truncate">{displayName} 님</div>
                {auth && (
                  <button onClick={() => setEditingNick(true)} title="닉네임 변경"
                    className="text-slate-500 hover:text-slate-300 transition-colors">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                  </button>
                )}
              </div>
            )}
            <div className="text-xs text-slate-400">{auth ? `@${auth.username}` : "게스트 모드"}</div>
          </div>
          <button onClick={onClose} className="ml-auto self-start">
            <X className="w-4 h-4 text-slate-500" />
          </button>
        </div>
        {auth && (
          <button onClick={handleLogout}
            className="mt-2 text-xs text-slate-400 hover:text-rose-400 transition-colors">
            로그아웃
          </button>
        )}
      </div>

      {/* 즐겨찾기 목록 */}
      <div className="px-4 py-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide flex items-center gap-1">
            <Star className="w-3 h-3 text-amber-400" /> 즐겨찾기 종목
          </span>
          <button onClick={() => setShowAdd(!showAdd)}
            className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
            <Plus className="w-3 h-3" /> 추가
          </button>
        </div>

        {/* 종목 추가 검색 */}
        {showAdd && (
          <div className="mb-3 relative">
            <input value={searchQ} onChange={e => setSearchQ(e.target.value)}
              placeholder="종목명 검색..."
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder:text-slate-500 outline-none focus:border-blue-500" />
            {filtered.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-700 rounded-lg z-10 max-h-36 overflow-y-auto">
                {filtered.map(s => (
                  <button key={s.symbol} onClick={() => add(s)}
                    className="w-full flex items-center justify-between px-3 py-2 text-xs hover:bg-slate-700 text-left">
                    <span className="text-slate-200">{s.name}</span>
                    <span className="text-slate-500 font-mono">{s.symbol}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 즐겨찾기 목록 */}
        <div className="space-y-1 max-h-72 overflow-y-auto">
          {favs.length === 0 ? (
            <div className="text-xs text-slate-500 text-center py-4">
              즐겨찾기 종목이 없어요
            </div>
          ) : favs.map(f => (
            <div key={f.symbol}
              className="flex items-center justify-between py-1.5 px-2 rounded-lg hover:bg-slate-800 transition-colors">
              <div>
                <span className="text-xs text-slate-200 font-medium">{f.name}</span>
                <span className="text-[10px] text-slate-500 ml-1.5 font-mono">{f.symbol}</span>
              </div>
              <button onClick={() => remove(f.symbol)}
                className="text-slate-600 hover:text-rose-400 transition-colors">
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


// ── 로그인 / 회원가입 모달 ─────────────────────────────────
function LoginModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: (user: AuthUser) => void }) {
  const [mode, setMode]       = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [nickname, setNicknameInput] = useState("");
  const [error, setError]     = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!username.trim() || !password.trim()) {
      setError("아이디와 비밀번호를 입력해주세요");
      return;
    }
    setLoading(true); setError("");
    try {
      const res = mode === "login"
        ? await login(username.trim(), password.trim())
        : await register(username.trim(), password.trim(), nickname.trim() || username.trim());

      if (res?.ok) {
        const { username: u, token, nickname: nick } = res.data;
        setAuth(u, token, nick);

        // 서버 즐겨찾기 → 로컬에 병합
        if (mode === "login" && res.data.favorites) {
          const localKey = "invest_nav_favorites";
          localStorage.setItem(localKey, JSON.stringify(res.data.favorites));
        }

        onSuccess({ username: u, nickname: nick || u, token });
        onClose();
      } else {
        setError(res?.error || "오류가 발생했습니다");
      }
    } catch {
      setError("서버 연결 오류");
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center" onClick={onClose}>
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-sm mx-4 shadow-2xl overflow-hidden"
        onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800">
          <span className="text-sm font-bold text-white">
            {mode === "login" ? "로그인" : "회원가입"}
          </span>
          <button onClick={onClose}><X className="w-4 h-4 text-slate-500" /></button>
        </div>

        <div className="p-5 space-y-3">
          <div>
            <label className="text-xs text-slate-400 mb-1 block">아이디</label>
            <input value={username} onChange={e => setUsername(e.target.value)}
              onKeyDown={e => e.key === "Enter" && submit()}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
              placeholder="아이디 입력" />
          </div>
          {mode === "register" && (
            <div>
              <label className="text-xs text-slate-400 mb-1 block">닉네임 (화면에 표시될 이름)</label>
              <input value={nickname} onChange={e => setNicknameInput(e.target.value)}
                onKeyDown={e => e.key === "Enter" && submit()}
                maxLength={12}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
                placeholder="닉네임 입력 (비워두면 아이디 사용)" />
            </div>
          )}
          <div>
            <label className="text-xs text-slate-400 mb-1 block">비밀번호</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)}
              onKeyDown={e => e.key === "Enter" && submit()}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
              placeholder="비밀번호 입력 (4자 이상)" />
          </div>

          {error && <p className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg p-2">{error}</p>}

          <button type="button" onClick={submit} disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-semibold rounded-lg px-4 py-2.5 transition-colors">
            {loading ? "처리 중..." : (mode === "login" ? "로그인" : "회원가입")}
          </button>

          <button type="button" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}
            className="w-full text-xs text-slate-400 hover:text-slate-300 transition-colors">
            {mode === "login" ? "계정이 없으신가요? 회원가입" : "이미 계정이 있으신가요? 로그인"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── 메인 레이아웃 ─────────────────────────────────────────
export function Layout({ children }: { children: React.ReactNode }) {
  const [location]             = useLocation();
  const [showSearch, setShowSearch] = useState(false);
  const [showNotif, setShowNotif]   = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [favCount, setFavCount]     = useState(getFavorites().length);
  const [showLogin, setShowLogin]   = useState(false);
  const [auth, setAuthState]        = useState(getAuth());
  const notifRef = useRef<HTMLDivElement>(null);

  // 즐겨찾기 개수 실시간 반영
  useEffect(() => {
    const interval = setInterval(() => setFavCount(getFavorites().length), 1000);
    return () => clearInterval(interval);
  }, []);

  // 키보드 단축키 (Cmd/Ctrl + K)
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setShowSearch(true);
      }
      if (e.key === "Escape") {
        setShowSearch(false);
        setShowNotif(false);
        setShowProfile(false);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* 검색 모달 */}
      {showSearch && <SearchModal onClose={() => setShowSearch(false)} />}

      {/* 로그인 모달 */}
      {showLogin && (
        <LoginModal
          onClose={() => setShowLogin(false)}
          onSuccess={(user) => setAuthState(user)}
        />
      )}

      {/* 사이드바 */}
      <aside className="w-44 flex flex-col border-r border-border bg-card shrink-0">
        {/* 로고 */}
        <div className="px-4 py-5 border-b border-border">
          <Link href="/">
            <div className="flex items-center gap-2 cursor-pointer">
              <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white text-xs font-bold shrink-0">투</div>
              <span className="text-sm font-bold text-white leading-tight">투자 내비게이터</span>
            </div>
          </Link>
        </div>

        {/* 네비게이션 */}
        <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map(({ icon: Icon, label, href }) => {
            const active = location === href;
            return (
              <Link key={href} href={href}>
                <div className={`flex items-center gap-2.5 px-3 py-2 rounded-lg cursor-pointer transition-colors text-sm
                  ${active
                    ? "bg-blue-600 text-white font-semibold"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"}`}>
                  <Icon className="w-4 h-4 shrink-0" />
                  <span className="leading-tight">{label}</span>
                </div>
              </Link>
            );
          })}
        </nav>

        {/* 프로필 */}
        <div className="px-2 py-3 border-t border-border relative">
          {auth ? (
            <button onClick={() => { setShowProfile(!showProfile); setShowNotif(false); }}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg hover:bg-slate-800 transition-colors">
              <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
                {auth.nickname.charAt(0)}
              </div>
              <div className="text-left min-w-0">
                <div className="text-xs font-semibold text-white truncate">{auth.nickname} 님</div>
                <div className="text-[10px] text-slate-500">로그인됨</div>
              </div>
            </button>
          ) : (
            <button onClick={() => setShowLogin(true)}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg hover:bg-slate-800 transition-colors">
              <div className="w-7 h-7 rounded-full bg-slate-700 flex items-center justify-center text-white text-xs font-bold shrink-0">?</div>
              <div className="text-left min-w-0">
                <div className="text-xs font-semibold text-white truncate">로그인 / 회원가입</div>
                <div className="text-[10px] text-slate-500">게스트 모드</div>
              </div>
            </button>
          )}
          {showProfile && <ProfilePanel onClose={() => setShowProfile(false)} />}
        </div>
      </aside>

      {/* 메인 영역 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* 상단 헤더 */}
        <header className="h-12 border-b border-border flex items-center justify-between px-6 shrink-0 bg-card">
          <h1 className="text-sm font-semibold text-white">
            {NAV_ITEMS.find(n => n.href === location)?.label || "대시보드"}
          </h1>
          <div className="flex items-center gap-2">
            {/* 돋보기 — 금융 백과사전 검색 */}
            <button onClick={() => setShowSearch(true)}
              className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 transition-colors relative"
              title="금융 용어 검색 (Ctrl+K)">
              <Search className="w-4 h-4" />
            </button>

            {/* 알림 — 즐겨찾기 뉴스 */}
            <div className="relative" ref={notifRef}>
              <button onClick={() => { setShowNotif(!showNotif); setShowProfile(false); }}
                className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 transition-colors relative"
                title="즐겨찾기 뉴스 알림">
                <Bell className="w-4 h-4" />
                {favCount > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-blue-600 rounded-full text-[9px] text-white flex items-center justify-center font-bold">
                    {favCount}
                  </span>
                )}
              </button>
              {showNotif && <NotificationPanel onClose={() => setShowNotif(false)} />}
            </div>
          </div>
        </header>

        {/* 콘텐츠 */}
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
