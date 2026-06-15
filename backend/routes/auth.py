"""
GET/POST /api/auth — 간단한 회원가입/로그인 시스템
SQLite 기반, 비밀번호는 해시 저장
"""
from flask import Blueprint, jsonify, request
import sqlite3
import hashlib
import secrets
import os
import json

auth_bp = Blueprint("auth", __name__)

# 영구 저장 시도: repo 상위 디렉토리(/data/tenants/<name>/) 우선 사용
# 컨테이너 재배포 시 repo/ 안의 파일은 git pull로 덮어써지지만
# repo 상위 디렉토리는 보존될 가능성이 있음
_REPO_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PARENT_DIR = os.path.dirname(_REPO_DIR)

_candidates = [
    os.path.join(_PARENT_DIR, "persistent_data", "users.db"),  # repo 밖 (영구 가능성)
    os.path.join(_REPO_DIR, "data", "users.db"),                # repo 안 (기존 위치, 폴백)
]

DB_PATH = _candidates[0]
try:
    os.makedirs(os.path.dirname(_candidates[0]), exist_ok=True)
    # 쓰기 테스트
    test_file = os.path.join(os.path.dirname(_candidates[0]), ".write_test")
    with open(test_file, "w") as f:
        f.write("test")
    os.remove(test_file)
except Exception:
    DB_PATH = _candidates[1]
    os.makedirs(os.path.dirname(_candidates[1]), exist_ok=True)


def _init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            token TEXT UNIQUE,
            favorites TEXT DEFAULT '[]',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


_init_db()


def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@auth_bp.post("/register")
def register():
    body = request.get_json(force=True)
    username = (body.get("username") or "").strip()
    password = (body.get("password") or "").strip()

    if not username or not password:
        return jsonify({"ok": False, "error": "아이디와 비밀번호를 입력해주세요"}), 400
    if len(username) < 2:
        return jsonify({"ok": False, "error": "아이디는 2자 이상이어야 합니다"}), 400
    if len(password) < 4:
        return jsonify({"ok": False, "error": "비밀번호는 4자 이상이어야 합니다"}), 400

    conn = _get_db()
    try:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            return jsonify({"ok": False, "error": "이미 존재하는 아이디입니다"}), 409

        pw_hash = _hash_pw(password)
        token   = secrets.token_hex(16)

        conn.execute(
            "INSERT INTO users (username, password_hash, token) VALUES (?, ?, ?)",
            (username, pw_hash, token),
        )
        conn.commit()

        return jsonify({"ok": True, "data": {"username": username, "token": token}})
    finally:
        conn.close()


@auth_bp.post("/login")
def login():
    body = request.get_json(force=True)
    username = (body.get("username") or "").strip()
    password = (body.get("password") or "").strip()

    conn = _get_db()
    try:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if not user or user["password_hash"] != _hash_pw(password):
            return jsonify({"ok": False, "error": "아이디 또는 비밀번호가 올바르지 않습니다"}), 401

        # 새 토큰 발급 (로그인마다 갱신)
        token = secrets.token_hex(16)
        conn.execute("UPDATE users SET token = ? WHERE id = ?", (token, user["id"]))
        conn.commit()

        favorites = json.loads(user["favorites"] or "[]")
        return jsonify({"ok": True, "data": {
            "username": username, "token": token, "favorites": favorites
        }})
    finally:
        conn.close()


@auth_bp.get("/me")
def me():
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not token:
        return jsonify({"ok": False, "error": "토큰 없음"}), 401

    conn = _get_db()
    try:
        user = conn.execute("SELECT * FROM users WHERE token = ?", (token,)).fetchone()
        if not user:
            return jsonify({"ok": False, "error": "유효하지 않은 토큰"}), 401

        favorites = json.loads(user["favorites"] or "[]")
        return jsonify({"ok": True, "data": {
            "username": user["username"], "favorites": favorites
        }})
    finally:
        conn.close()


@auth_bp.post("/favorites")
def update_favorites():
    """즐겨찾기 동기화 — 토큰 기반"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not token:
        return jsonify({"ok": False, "error": "토큰 없음"}), 401

    body = request.get_json(force=True)
    favorites = body.get("favorites", [])

    conn = _get_db()
    try:
        user = conn.execute("SELECT id FROM users WHERE token = ?", (token,)).fetchone()
        if not user:
            return jsonify({"ok": False, "error": "유효하지 않은 토큰"}), 401

        conn.execute(
            "UPDATE users SET favorites = ? WHERE id = ?",
            (json.dumps(favorites, ensure_ascii=False), user["id"]),
        )
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()

@auth_bp.get("/debug-path")
def debug_path():
    """DB 경로 디버그용"""
    return jsonify({
        "ok": True,
        "db_path": DB_PATH,
        "exists": os.path.exists(DB_PATH),
        "repo_dir": _REPO_DIR,
        "parent_dir": _PARENT_DIR,
        "parent_writable": os.access(_PARENT_DIR, os.W_OK),
    })
