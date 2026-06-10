"""
GET /api/stocks/search?q=...         종목 검색
GET /api/stocks/<symbol>             종목 정보
GET /api/stocks/<symbol>/history     과거 주가 (period 쿼리)
"""
from flask import Blueprint, request, jsonify
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.stock_data import search_stocks, get_stock_info, get_historical_data, PERIOD_MAP

stocks_bp = Blueprint("stocks", __name__)


@stocks_bp.get("/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"ok": False, "error": "q 파라미터 필요"}), 400
    results = search_stocks(q)
    return jsonify({"ok": True, "data": results})


@stocks_bp.get("/<symbol>")
def stock_info(symbol):
    try:
        info = get_stock_info(symbol)
        return jsonify({"ok": True, "data": info})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@stocks_bp.get("/<symbol>/history")
def stock_history(symbol):
    period_label = request.args.get("period", "1년")
    period = PERIOD_MAP.get(period_label, "1y")
    try:
        hist = get_historical_data(symbol, period)
        if hist is None or hist.empty:
            return jsonify({"ok": True, "data": []})
        records = [
            {
                "date":   str(idx.date()),
                "open":   round(float(row["Open"]),  2),
                "high":   round(float(row["High"]),  2),
                "low":    round(float(row["Low"]),   2),
                "close":  round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            }
            for idx, row in hist.iterrows()
        ]
        return jsonify({"ok": True, "data": records})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
