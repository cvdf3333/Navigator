"""
GET/POST /api/auth — 간단한 회원가입/로그인 시스템
SQLite 기반, 비밀번호는 해시 저장
DB는 GitHub repo의 data/users.db에 자동 커밋되어 영구 보존됨
"""
from flask import Blueprint, jsonify, request
import sqlite3
import hashlib
import secrets
import os
import json
import shutil
import threading

auth_bp = Blueprint("auth", __name__)

# ── 경로 설정 ────────────────────────────────────────────
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
_REPO_DIR    = os.path.dirname(_BACKEND_DIR)                                 # repo root

# 컨테이너 재배포 시 보존 가능성이 있는 경로 (repo 밖)
_PERSIST_DB = os.path.join(os.path.dirname(_REPO_DIR), "persistent_data", "users.db")
# git에 커밋되는 경로 (repo 안, 재배포 시 git pull로 복원됨)
_TRACKED_DB = os.path.join(_REPO_DIR, "data", "users.db")

# 실제 작업용 DB 경로: persistent 우선, 실패하면 tracked 사용
DB_PATH = _PERSIST_DB
try:
    os.makedirs(os.path.dirname(_PERSIST_DB), exist_ok=True)
    test_file = os.path.join(os.path.dirname(_PERSIST_DB), ".write_test")
    with open(test_file, "w") as f:
        f.write("test")
    os.remove(test_file)
except Exception:
    DB_PATH = _TRACKED_DB
    os.makedirs(os.path.dirname(_TRACKED_DB), exist_ok=True)


def _init_db():
    if DB_PATH == _PERSIST_DB and not os.path.exists(_PERSIST_DB) and os.path.exists(_TRACKED_DB):
        try:
            shutil.copy(_TRACKED_DB, _PERSIST_DB)
        except Exception:
            pass

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
    try:
        conn.execute("ALTER TABLE users ADD COLUMN nickname TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


_init_db()


def _hash_pw(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _git_push_db():
    """DB 변경사항을 GitHub API로 직접 업로드 (영구 저장용, 실패해도 무시)"""
    import base64
    import requests as req

    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("GITHUB_REPO", "")
    if not token or not repo:
        return

    try:
        with open(DB_PATH, "rb") as f:
            content_b64 = base64.b64encode(f.read()).decode("utf-8")

        api_url = "https://api.github.com/repos/" + repo + "/contents/data/users.db"
        headers = {
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
        }

        # 기존 파일의 sha 확인 (있으면 업데이트, 없으면 생성)
        get_res = req.get(api_url, headers=headers, timeout=10)
        sha = get_res.json().get("sha") if get_res.status_code == 200 else None

        payload = {
            "message": "auto: update users.db",
            "content": content_b64,
            "branch": "main",
        }
        if sha:
            payload["sha"] = sha

        put_res = req.put(api_url, headers=headers, json=payload, timeout=15)
        if put_res.status_code not in (200, 201):
            print("[git_push_db] GitHub API 오류: " + str(put_res.status_code) + " " + put_res.text[:300])
    except Exception as e:
        print("[git_push_db] 오류 (무시됨): " + str(e))

def _git_push_db_async():
    threading.Thread(target=_git_push_db, daemon=True).start()


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

        nickname = (body.get("nickname") or username).strip()
        pw_hash = _hash_pw(password)
        token = secrets.token_hex(16)

        conn.execute(
            "INSERT INTO users (username, password_hash, nickname, token) VALUES (?, ?, ?, ?)",
            (username, pw_hash, nickname, token),
        )
        conn.commit()
        _git_push_db_async()

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

        token = secrets.token_hex(16)
        conn.execute("UPDATE users SET token = ? WHERE id = ?", (token, user["id"]))
        conn.commit()
        _git_push_db_async()

        favorites = json.loads(user["favorites"] or "[]")
        nickname = user["nickname"] or username
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
            "username": user["username"],
            "nickname": user["nickname"] or user["username"],
            "favorites": favorites
        }})
    finally:
        conn.close()


@auth_bp.post("/favorites")
def update_favorites():
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
        _git_push_db_async()
        return jsonify({"ok": True})
    finally:
        conn.close()


@auth_bp.post("/nickname")
def update_nickname():
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
        _git_push_db_async()
        return jsonify({"ok": True, "data": {"nickname": nickname}})
    finally:
        conn.close()


@auth_bp.get("/debug-path")
def debug_path():
    """DB 경로 디버그용"""
    return jsonify({
        "ok": True,
        "db_path": DB_PATH,
        "exists": os.path.exists(DB_PATH),
        "tracked_db": _TRACKED_DB,
        "tracked_exists": os.path.exists(_TRACKED_DB),
        "repo_dir": _REPO_DIR,
        "github_configured": bool(os.environ.get("GITHUB_TOKEN") and os.environ.get("GITHUB_REPO")),
    })


@auth_bp.get("/debug-git-push")
def debug_git_push():
    """GitHub API push 과정을 동기적으로 실행하고 결과 반환 (디버그용)"""
    import base64
    import requests as req

    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("GITHUB_REPO", "")

    if not token or not repo:
        return jsonify({"ok": False, "error": "GITHUB_TOKEN 또는 GITHUB_REPO 미설정"})

    try:
        with open(DB_PATH, "rb") as f:
            content_b64 = base64.b64encode(f.read()).decode("utf-8")

        api_url = "https://api.github.com/repos/" + repo + "/contents/data/users.db"
        headers = {
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
        }

        get_res = req.get(api_url, headers=headers, timeout=10)
        sha = get_res.json().get("sha") if get_res.status_code == 200 else None

        payload = {
            "message": "auto: update users.db",
            "content": content_b64,
            "branch": "main",
        }
        if sha:
            payload["sha"] = sha

        put_res = req.put(api_url, headers=headers, json=payload, timeout=15)

        return jsonify({
            "ok": put_res.status_code in (200, 201),
            "get_status": get_res.status_code,
            "put_status": put_res.status_code,
            "put_response": put_res.json() if put_res.status_code not in (200, 201) else "success",
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})
