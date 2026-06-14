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

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "users.db")


def _init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nickname TEXT,
            token TEXT UNIQUE,
            favorites TEXT DEFAULT '[]',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 기존 DB에 nickname 컬럼이 없으면 추가 (마이그레이션)
    try:
        conn.execute("ALTER TABLE users ADD COLUMN nickname TEXT")
    except sqlite3.OperationalError:
        pass  # 이미 존재함
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

        nickname = (body.get("nickname") or username).strip()

        conn.execute(
            "INSERT INTO users (username, password_hash, nickname, token) VALUES (?, ?, ?, ?)",
            (username, pw_hash, nickname, token),
        )
        conn.commit()

        return jsonify({"ok": True, "data": {"username": username, "nickname": nickname, "token": token}})
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
        nickname  = user["nickname"] or username
        return jsonify({"ok": True, "data": {
            "username": username, "nickname": nickname, "token": token, "favorites": favorites
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
            "username": user["username"], "nickname": user["nickname"] or user["username"], "favorites": favorites
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

@auth_bp.post("/nickname")
def update_nickname():
    """닉네임 변경"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not token:
        return jsonify({"ok": False, "error": "토큰 없음"}), 401

    body = request.get_json(force=True)
    nickname = (body.get("nickname") or "").strip()

    if not nickname or len(nickname) < 1 or len(nickname) > 12:
        return jsonify({"ok": False, "error": "닉네임은 1~12자여야 합니다"}), 400

    conn = _get_db()
    try:
        user = conn.execute("SELECT id FROM users WHERE token = ?", (token,)).fetchone()
        if not user:
            return jsonify({"ok": False, "error": "유효하지 않은 토큰"}), 401

        conn.execute("UPDATE users SET nickname = ? WHERE id = ?", (nickname, user["id"]))
        conn.commit()
        return jsonify({"ok": True, "data": {"nickname": nickname}})
    finally:
        conn.close()
