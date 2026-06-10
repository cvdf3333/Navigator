"""
GET /api/disclosure/<corp_name>?limit=10
"""
from flask import Blueprint, request, jsonify
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.dart_api import get_corp_code_cached, get_recent_disclosures

disclosure_bp = Blueprint("disclosure", __name__)


@disclosure_bp.get("/<corp_name>")
def get_disclosures(corp_name):
    limit = int(request.args.get("limit", 10))
    try:
        corp_code = get_corp_code_cached(corp_name)
        if not corp_code:
            return jsonify({"ok": False, "error": f"'{corp_name}' DART 코드 없음", "data": []}), 404
        data = get_recent_disclosures(corp_code, limit=limit)
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "data": []}), 500
