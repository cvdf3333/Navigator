// 즐겨찾기 종목 관리 (localStorage 기반)
export interface FavoriteStock {
  symbol: string;
  name: string;
  market: string;
  addedAt: string;
}

const KEY = "invest_nav_favorites";

export function getFavorites(): FavoriteStock[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) || "[]");
  } catch { return []; }
}

export function addFavorite(stock: Omit<FavoriteStock, "addedAt">) {
  const favs = getFavorites();
  if (favs.find(f => f.symbol === stock.symbol)) return;
  favs.push({ ...stock, addedAt: new Date().toISOString() });
  localStorage.setItem(KEY, JSON.stringify(favs));
}

export function removeFavorite(symbol: string) {
  const favs = getFavorites().filter(f => f.symbol !== symbol);
  localStorage.setItem(KEY, JSON.stringify(favs));
}

export function isFavorite(symbol: string): boolean {
  return getFavorites().some(f => f.symbol === symbol);
}
