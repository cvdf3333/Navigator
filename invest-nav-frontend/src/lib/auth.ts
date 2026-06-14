// 간단한 인증 관리 (localStorage 토큰 기반)
const TOKEN_KEY = "invest_nav_token";
const USER_KEY  = "invest_nav_username";
const NICK_KEY  = "invest_nav_nickname";

export interface AuthUser {
  username: string;
  nickname: string;
  token: string;
}

export function getAuth(): AuthUser | null {
  const token    = localStorage.getItem(TOKEN_KEY);
  const username = localStorage.getItem(USER_KEY);
  const nickname = localStorage.getItem(NICK_KEY);
  if (!token || !username) return null;
  return { username, nickname: nickname || username, token };
}

export function setAuth(username: string, token: string, nickname?: string) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, username);
  localStorage.setItem(NICK_KEY, nickname || username);
}

export function setNickname(nickname: string) {
  localStorage.setItem(NICK_KEY, nickname);
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(NICK_KEY);
}

export function isLoggedIn(): boolean {
  return getAuth() !== null;
}

export async function register(username: string, password: string, nickname?: string) {
  const res = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, nickname: nickname || username }),
  });
  return res.json();
}

export async function login(username: string, password: string) {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return res.json();
}

export async function syncFavorites(favorites: any[]) {
  const auth = getAuth();
  if (!auth) return;
  await fetch("/api/auth/favorites", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${auth.token}`,
    },
    body: JSON.stringify({ favorites }),
  });
}

export async function fetchServerFavorites() {
  const auth = getAuth();
  if (!auth) return null;
  const res = await fetch("/api/auth/me", {
    headers: { "Authorization": `Bearer ${auth.token}` },
  });
  const data = await res.json();
  return data?.ok ? data.data.favorites : null;
}

export async function updateNickname(nickname: string) {
  const auth = getAuth();
  if (!auth) return { ok: false, error: "로그인 필요" };
  const res = await fetch("/api/auth/nickname", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${auth.token}`,
    },
    body: JSON.stringify({ nickname }),
  });
  return res.json();
}
