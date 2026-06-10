"""
GET    /api/memo/            메모 목록
POST   /api/memo/            새 메모 생성
PUT    /api/memo/<id>        메모 수정
DELETE /api/memo/<id>        메모 삭제
"""
from flask import Blueprint, request, jsonify
import json, os
from datetime import datetime

memo_bp = Blueprint("memo", __name__)

# data/ 디렉토리 기준 (start.py가 프로젝트 루트에서 실행)
DATA_DIR  = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
MEMO_FILE = os.path.join(DATA_DIR, "memos.json")
os.makedirs(DATA_DIR, exist_ok=True)


def _load():
    if os.path.exists(MEMO_FILE):
        try:
            with open(MEMO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _save(memos):
    with open(MEMO_FILE, "w", encoding="utf-8") as f:
        json.dump(memos, f, ensure_ascii=False, indent=2)


@memo_bp.get("/")
def list_memos():
    return jsonify({"ok": True, "data": _load()})


@memo_bp.post("/")
def create_memo():
    body = request.get_json(force=True)
    memos = _load()
    memo = {
        "id":        datetime.now().isoformat(),
        "stock":     body.get("stock", ""),
        "title":     body.get("title", ""),
        "sections":  body.get("sections", {}),
        "tags":      body.get("tags", []),
        "createdAt": datetime.now().strftime("%Y-%m-%d"),
        "updatedAt": datetime.now().strftime("%Y-%m-%d"),
    }
    memos.append(memo)
    _save(memos)
    return jsonify({"ok": True, "data": memo}), 201


@memo_bp.put("/<memo_id>")
def update_memo(memo_id):
    body  = request.get_json(force=True)
    memos = _load()
    updated = None
    for m in memos:
        if m["id"] == memo_id:
            m.update({k: v for k, v in body.items() if k != "id"})
            m["updatedAt"] = datetime.now().strftime("%Y-%m-%d")
            updated = m
            break
    if not updated:
        return jsonify({"ok": False, "error": "메모 없음"}), 404
    _save(memos)
    return jsonify({"ok": True, "data": updated})


@memo_bp.delete("/<memo_id>")
def delete_memo(memo_id):
    memos = _load()
    new   = [m for m in memos if m["id"] != memo_id]
    if len(new) == len(memos):
        return jsonify({"ok": False, "error": "메모 없음"}), 404
    _save(new)
    return jsonify({"ok": True})
