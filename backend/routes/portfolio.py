"""
POST /api/portfolio/analyze
body: { holdings: [{symbol, name, weight, market}], investment_type: "auto" }
"""
from flask import Blueprint, request, jsonify
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.portfolio import (
    compute_rr_score, compute_scenarios,
    compute_sector_allocation, infer_investment_type,
    backtest_portfolio, INVESTMENT_TYPE_LABEL,
)

portfolio_bp = Blueprint("portfolio", __name__)


@portfolio_bp.post("/analyze")
def analyze():
    body     = request.get_json(force=True)
    holdings = body.get("holdings", [])
    inv_type = body.get("investment_type", "auto")

    if not holdings:
        return jsonify({"ok": False, "error": "holdings 필요"}), 400

    try:
        inferred    = infer_investment_type(holdings)
        effective   = inferred if inv_type == "auto" else inv_type
        rr          = compute_rr_score(holdings, investment_type=effective)
        scenarios   = compute_scenarios(rr, investment_type=effective)
        sector_alloc= compute_sector_allocation(holdings)

        domestic = sum(h["weight"] for h in holdings if h.get("market") in ["KRX", "KOSDAQ"])
        foreign  = 100 - domestic

        recommendations = []
        if len(sector_alloc) < 3:
            recommendations.append("⚠️ 섹터 집중도가 높습니다. 다양한 섹터로 분산을 권장합니다.")
        if len(holdings) < 5:
            recommendations.append("📌 종목 수가 적습니다. 5~15개 종목 보유를 권장합니다.")
        if domestic > 80:
            recommendations.append("🌍 국내 비중이 높습니다. 해외 자산 10~30% 편입을 고려하세요.")
        if foreign > 70:
            recommendations.append("🏠 해외 비중이 높습니다. 환헤지 전략 또는 국내 자산 편입을 검토하세요.")
        if rr["score"] < 4:
            recommendations.append("📉 R/R Score가 낮습니다. 포트폴리오 재구성을 권장합니다.")
        if not recommendations:
            recommendations.append("✅ 포트폴리오 구성이 양호합니다. 정기적 리밸런싱을 권장합니다.")
        label_map = {"aggressive": "공격투자형", "balanced": "위험중립형", "conservative": "안정추구형"}
        recommendations.append(f"📊 분석된 투자 성향: {label_map.get(inferred, inferred)}")

        return jsonify({
            "ok": True,
            "rr":            rr,
            "scenarios":     scenarios,
            "sector_alloc":  sector_alloc,
            "inferred":      inferred,
            "domestic":      domestic,
            "foreign":       foreign,
            "recommendations": recommendations,
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@portfolio_bp.post("/backtest")
def backtest():
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
