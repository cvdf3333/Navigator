// 즐겨찾기 종목 관리 (localStorage 기반)
export interface FavoriteStock {
  symbol: string;
  name: string;
  market: string;
  addedAt: string;
}

const KEY = "invest_nav_favorites";

export function getFavorites(): FavoriteStock[] {
  // 로그인 안 된 게스트는 항상 빈 목록
  try {
    const token = localStorage.getItem("invest_nav_token");
    if (!token) return [];
    return JSON.parse(localStorage.getItem(KEY) || "[]");
  } catch { return []; }
}

export function addFavorite(stock: Omit<FavoriteStock, "addedAt">) {
  const favs = getFavorites();
  if (favs.find(f => f.symbol === stock.symbol)) return;
  favs.push({ ...stock, addedAt: new Date().toISOString() });
  localStorage.setItem(KEY, JSON.stringify(favs));
  _syncToServer(favs);
}

export function removeFavorite(symbol: string) {
  const favs = getFavorites().filter(f => f.symbol !== symbol);
  localStorage.setItem(KEY, JSON.stringify(favs));
  _syncToServer(favs);
}

// 로그인된 경우 서버에 동기화 (비동기, 실패해도 무시)
function _syncToServer(favs: FavoriteStock[]) {
  import("./auth").then(({ syncFavorites }) => {
    syncFavorites(favs).catch(() => {});
  });
}

export function isFavorite(symbol: string): boolean {
  return getFavorites().some(f => f.symbol === symbol);
}
