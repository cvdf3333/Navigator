"""
POST /api/news/   body: {symbol, limit}
GET  /api/news/<symbol>?limit=10
"""
from flask import Blueprint, request, jsonify
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.news_crawler import crawl_naver_news, analyze_news_sentiment

news_bp = Blueprint("news", __name__)


@news_bp.get("/<symbol>")
def get_news(symbol):
    limit = int(request.args.get("limit", 10))

    # "market" 은 특정 종목이 아니라 전체 시장 뉴스를 의미
    # → 코스피/증시 키워드로 검색
    search_symbol = "코스피 증시" if symbol == "market" else symbol

    try:
        news_list = crawl_naver_news(search_symbol, limit)
        sentiment = analyze_news_sentiment(news_list)
        return jsonify({"ok": True, "data": news_list, "sentiment": sentiment})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "data": [], "sentiment": {}}), 500


@news_bp.post("/")
def post_news():
    body   = request.get_json(force=True)
    symbol = body.get("symbol", "")
    limit  = int(body.get("limit", 10))
    try:
        news_list = crawl_naver_news(symbol, limit)
        sentiment = analyze_news_sentiment(news_list)
        return jsonify({"ok": True, "data": news_list, "sentiment": sentiment})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "data": [], "sentiment": {}}), 500
