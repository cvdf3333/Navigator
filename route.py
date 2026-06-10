"""
투자 내비게이터 v2.0 — 시연 환경 route.py
cau19 전용: https://www.eyefeet.com/cau19/py/
"""
import sys
import os
import subprocess

# ── 필수 패키지 자동 설치 ─────────────────────────────────
_REQUIRED = [
    "yfinance",
    "beautifulsoup4",
    "lxml",
    "requests",
    "pandas",
    "numpy",
    "python-dotenv",
]

def _ensure_packages():
    """서버에 패키지가 없으면 자동으로 설치"""
    for pkg in _REQUIRED:
        import_name = {
            "beautifulsoup4": "bs4",
            "python-dotenv":  "dotenv",
        }.get(pkg, pkg.replace("-", "_"))
        try:
            __import__(import_name)
        except ImportError:
            print(f"[install] {pkg} 설치 중...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg,
                 "--quiet", "--no-warn-script-location",
                 "--user"],
                check=False,
                capture_output=True,
            )

_ensure_packages()

# ── .env 로드 ─────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    pass

from flask import jsonify, request

# ── dist/ 정적 파일 서빙 (React 빌드 결과물) ─────────────
from flask import send_from_directory, send_file

DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")

@bp.route("/")
def serve_index():
    if os.path.exists(os.path.join(DIST_DIR, "index.html")):
        return send_file(os.path.join(DIST_DIR, "index.html"))
    return jsonify({"ok": True, "message": "투자 내비게이터 API v2.0"})

@bp.route("/health")
def health():
    return jsonify({"ok": True, "status": "running", "dist": os.path.exists(DIST_DIR)})

@bp.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(os.path.join(DIST_DIR, "assets"), filename)

@bp.route("/app/<path:path>")
def serve_static(path):
    file_path = os.path.join(DIST_DIR, path)
    if os.path.exists(file_path):
        return send_from_directory(DIST_DIR, path)
    return send_file(os.path.join(DIST_DIR, "index.html"))


# utils 경로 추가 (py/ 폴더 기준)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── 유틸리티 임포트 ──────────────────────────────────────
try:
    from utils.stock_data   import get_macro_data
    from utils.news_crawler import crawl_naver_news, analyze_news_sentiment
    from utils.portfolio    import (
        compute_rr_score, compute_scenarios,
        compute_sector_allocation, infer_investment_type,
        backtest_portfolio,
    )
    from utils.dart_api import get_dart_disclosure
    import yfinance as yf
    import pandas as pd
    import math
    UTILS_OK = True
except ImportError as e:
    UTILS_OK = False
    IMPORT_ERROR = str(e)


def _safe(val):
    if val is None: return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f): return None
        return f
    except: return None


# ── 헬스 체크 ────────────────────────────────────────────


# ── 거시경제 지표 ─────────────────────────────────────────
@bp.route("/macro")
def macro():
    if not UTILS_OK:
        return jsonify({"ok": False, "error": IMPORT_ERROR}), 500
    try:
        data = get_macro_data()
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@bp.route("/macro/analysis")
def macro_analysis():
    if not UTILS_OK:
        return jsonify({"ok": False, "error": IMPORT_ERROR}), 500
    result = {}
    try:
        # 코스피 달러 환산
        kospi_s  = yf.Ticker("^KS11").history(period="1y")["Close"].dropna()
        usdkrw_s = yf.Ticker("KRW=X").history(period="1y")["Close"].dropna()
        if not kospi_s.empty and not usdkrw_s.empty:
            usdkrw_r = usdkrw_s.reindex(kospi_s.index, method="ffill").dropna()
            kospi_r  = kospi_s.reindex(usdkrw_r.index).dropna()
            kospi_usd = (kospi_r / usdkrw_r).dropna()
            result["kospi_usd"] = {
                "current_krw": round(float(kospi_s.iloc[-1]), 2),
                "current_usd": round(float(kospi_usd.iloc[-1]), 4) if not kospi_usd.empty else None,
                "usdkrw":      round(float(usdkrw_s.iloc[-1]), 2),
                "description": "코스피 지수를 현재 환율로 달러 환산한 실질 가치",
            }
    except Exception as e:
        result["kospi_usd"] = {"error": str(e)}

    try:
        # 반도체 쏠림
        syms = {"kospi": "^KS11", "samsung": "005930.KS", "skhynix": "000660.KS"}
        data_s = {}
        for key, sym in syms.items():
            h = yf.Ticker(sym).history(period="3mo")["Close"].dropna()
            if len(h) >= 2:
                data_s[key] = round((float(h.iloc[-1]) / float(h.iloc[0]) - 1) * 100, 2)
        kospi_r = data_s.get("kospi", 0)
        sam_r   = data_s.get("samsung", 0)
        hyn_r   = data_s.get("skhynix", 0)
        semicon = round(sam_r * 0.18 + hyn_r * 0.10, 2)
        others  = round(kospi_r - semicon, 2)
        ratio   = round(abs(semicon / kospi_r * 100), 1) if kospi_r != 0 else 0
        result["semiconductor_skew"] = {
            "kospi_return": kospi_r, "samsung_return": sam_r, "skhynix_return": hyn_r,
            "semicon_contribution": semicon, "others_contribution": others,
            "semicon_ratio_pct": ratio, "period": "최근 3개월",
            "description": "반도체 2종목이 코스피 상승에 기여한 비중",
        }
    except Exception as e:
        result["semiconductor_skew"] = {"error": str(e)}

    try:
        # DXY 분석
        dxy_s   = yf.Ticker("DX-Y.NYB").history(period="1y")["Close"].dropna()
        kospi_s = yf.Ticker("^KS11").history(period="1y")["Close"].dropna()
        if not dxy_s.empty and not kospi_s.empty:
            dxy_r = dxy_s.pct_change().dropna()
            ksp_r = kospi_s.reindex(dxy_s.index, method="ffill").pct_change().dropna()
            common = dxy_r.index.intersection(ksp_r.index)
            corr = float(dxy_r[common].corr(ksp_r[common])) if len(common) > 5 else None
            dxy_cur = float(dxy_s.iloc[-1])
            dxy_1y  = round((dxy_cur / float(dxy_s.iloc[0]) - 1) * 100, 2)
            result["dxy_analysis"] = {
                "dxy_current": round(dxy_cur, 2), "dxy_1y_change": dxy_1y,
                "kospi_dxy_corr": round(corr, 4) if corr else None,
                "interpretation": "음수(-): 달러 강세 시 코스피 하락 경향" if corr and corr < 0 else "양수(+): 달러와 코스피 동반 상승",
                "description": "달러 인덱스와 코스피의 상관관계 분석",
            }
    except Exception as e:
        result["dxy_analysis"] = {"error": str(e)}

    result["investor_returns"] = {
        "description": "투자자 유형별 연간 수익률 비교",
        "data": [
            {"year": 2020, "individual": 43.2, "institutional": 18.7, "foreign": 7.8},
            {"year": 2021, "individual": -8.4, "institutional": 5.2,  "foreign": 12.3},
            {"year": 2022, "individual": -28.1,"institutional": -19.4,"foreign": -22.6},
            {"year": 2023, "individual": 12.4, "institutional": 21.8, "foreign": 19.2},
            {"year": 2024, "individual": -5.2, "institutional": 3.1,  "foreign": 8.7},
        ],
        "insight": "개인 투자자는 변동성이 크고 장기적으로 기관·외국인 대비 수익률이 낮은 경향이 있습니다.",
    }
    result["realestate_effect"] = {
        "description": "부동산 규제 강화 시기와 주식시장 자금 유입 상관관계",
        "events": [
            {"year": 2020, "policy": "부동산 투기과열지구 확대",  "kospi_change": "+30.8%", "note": "개인투자자 주식 순매수 급증"},
            {"year": 2021, "policy": "대출 규제 강화 (DSR 도입)", "kospi_change": "+3.6%",  "note": "동학개미운동 절정"},
            {"year": 2022, "policy": "금리 인상 + 부동산 하락",   "kospi_change": "-24.9%", "note": "증시·부동산 동반 하락"},
            {"year": 2023, "policy": "특례보금자리론 출시",        "kospi_change": "+18.7%", "note": "부동산 회복 + 증시 반등"},
        ],
        "insight": "부동산 진입 장벽이 높아질수록 유동자금이 주식시장으로 유입되는 경향이 있습니다.",
    }
    return jsonify({"ok": True, "data": result})


# ── 뉴스 ─────────────────────────────────────────────────
@bp.route("/news/<symbol>")
def get_news(symbol):
    if not UTILS_OK:
        return jsonify({"ok": False, "error": IMPORT_ERROR, "data": [], "sentiment": {}}), 500
    limit = int(request.args.get("limit", 10))
    try:
        news_list = crawl_naver_news(symbol, limit)
        sentiment = analyze_news_sentiment(news_list)
        return jsonify({"ok": True, "data": news_list, "sentiment": sentiment})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "data": [], "sentiment": {}}), 500


@bp.route("/news/market")
def get_market_news():
    if not UTILS_OK:
        return jsonify({"ok": False, "data": []}), 500
    limit = int(request.args.get("limit", 4))
    try:
        news_list = crawl_naver_news("005930.KS", limit)
        return jsonify({"ok": True, "data": news_list})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "data": []}), 500


# ── 공시 ─────────────────────────────────────────────────
@bp.route("/disclosure/<corp_name>")
def get_disclosure(corp_name):
    if not UTILS_OK:
        return jsonify({"ok": False, "data": []}), 500
    limit = int(request.args.get("limit", 10))
    try:
        data = get_dart_disclosure(corp_name, limit=limit)
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "data": []}), 500


# ── 포트폴리오 분석 ───────────────────────────────────────
@bp.route("/portfolio/analyze", methods=["POST"])
def analyze_portfolio():
    if not UTILS_OK:
        return jsonify({"ok": False, "error": IMPORT_ERROR}), 500
    body     = request.get_json(force=True)
    holdings = body.get("holdings", [])
    inv_type = body.get("investment_type", "auto")
    if not holdings:
        return jsonify({"ok": False, "error": "holdings 필요"}), 400
    try:
        inferred     = infer_investment_type(holdings)
        effective    = inferred if inv_type == "auto" else inv_type
        rr           = compute_rr_score(holdings, investment_type=effective)
        scenarios    = compute_scenarios(rr, investment_type=effective)
        sector_alloc = compute_sector_allocation(holdings)
        domestic = sum(h["weight"] for h in holdings if h.get("market") in ["KRX", "KOSDAQ"])
        foreign  = 100 - domestic
        recommendations = []
        if len(sector_alloc) < 3:
            recommendations.append("⚠️ 섹터 집중도가 높습니다. 다양한 섹터로 분산을 권장합니다.")
        if len(holdings) < 5:
            recommendations.append("📌 종목 수가 적습니다. 5~15개 종목 보유를 권장합니다.")
        if domestic > 80:
            recommendations.append("🌍 국내 비중이 높습니다. 해외 자산 10~30% 편입을 고려하세요.")
        if rr["score"] < 4:
            recommendations.append("📉 R/R Score가 낮습니다. 포트폴리오 재구성을 권장합니다.")
        if not recommendations:
            recommendations.append("✅ 포트폴리오 구성이 양호합니다. 정기적 리밸런싱을 권장합니다.")
        return jsonify({
            "ok": True, "rr": rr, "scenarios": scenarios,
            "sector_alloc": sector_alloc, "inferred": inferred,
            "domestic": domestic, "foreign": foreign,
            "recommendations": recommendations,
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ── 백테스팅 ──────────────────────────────────────────────
@bp.route("/portfolio/backtest", methods=["POST"])
def backtest():
    if not UTILS_OK:
        return jsonify({"ok": False, "error": IMPORT_ERROR}), 500
    from datetime import datetime
    body     = request.get_json(force=True)
    holdings = body.get("holdings", [])
    start    = datetime.fromisoformat(body.get("start_date"))
    end      = datetime.fromisoformat(body.get("end_date"))
    amount   = int(body.get("initial_amount", 10_000_000))
    bench    = body.get("benchmark", "^GSPC")
    try:
        result = backtest_portfolio(holdings, start, end, amount, bench)
        return jsonify({"ok": True, "data": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
