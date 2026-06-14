"""GET /api/macro        — 거시경제 기본 지표
   GET /api/macro/analysis — 교수님 피드백 심화 분석
"""
from flask import Blueprint, jsonify
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.stock_data import get_macro_data
import yfinance as yf
import pandas as pd
import math

macro_bp = Blueprint("macro", __name__)


def _safe(val) -> float | None:
    """NaN / inf / None 을 모두 None으로 변환"""
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except Exception:
        return None


def _get_close(sym: str, period: str = "3mo") -> pd.Series | None:
    """
    yfinance MultiIndex 컬럼 대응 Close 시리즈 반환.
    데이터가 없거나 NaN이면 None 반환.
    """
    try:
        hist = yf.Ticker(sym).history(period=period)
        if hist is None or hist.empty:
            return None

        # MultiIndex 컬럼 처리 (yfinance 최신 버전 대응)
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = [c[0] for c in hist.columns]

        if "Close" not in hist.columns:
            return None

        close = hist["Close"].dropna()
        if close.empty:
            return None

        # 타임존 제거
        if hasattr(close.index, "tz") and close.index.tz is not None:
            close.index = close.index.tz_localize(None)

        return close
    except Exception:
        return None


def _pct_return(series: pd.Series) -> float | None:
    """시리즈 처음~끝 수익률 (%)"""
    if series is None or len(series) < 2:
        return None
    start = _safe(series.iloc[0])
    end   = _safe(series.iloc[-1])
    if start is None or end is None or start == 0:
        return None
    return round((end / start - 1) * 100, 2)

@macro_bp.get("")
@macro_bp.get("/")
def macro():
    try:
        data = get_macro_data()
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@macro_bp.get("/analysis")
def macro_analysis():
    """교수님 피드백 반영 심화 분석 지표"""
    result = {}

    # ① 코스피 달러 환산 실질 가치
    try:
        kospi_s  = _get_close("^KS11",  "1y")
        usdkrw_s = _get_close("KRW=X",  "1y")

        if kospi_s is not None and usdkrw_s is not None:
            usdkrw_r = usdkrw_s.reindex(kospi_s.index, method="ffill").dropna()
            kospi_r  = kospi_s.reindex(usdkrw_r.index).dropna()
            kospi_usd = (kospi_r / usdkrw_r).dropna()

            krw_val = _safe(kospi_s.iloc[-1])
            usd_val = _safe(kospi_usd.iloc[-1]) if not kospi_usd.empty else None
            fx_val  = _safe(usdkrw_s.iloc[-1])

            if krw_val and usd_val and fx_val:
                result["kospi_usd"] = {
                    "current_krw": round(krw_val, 2),
                    "current_usd": round(usd_val, 4),
                    "usdkrw":      round(fx_val, 2),
                    "description": "코스피 지수를 현재 환율로 달러 환산한 실질 가치",
                }
            else:
                result["kospi_usd"] = {"error": "데이터 변환 실패 (NaN)"}
        else:
            result["kospi_usd"] = {"error": "yfinance 데이터 없음"}
    except Exception as e:
        result["kospi_usd"] = {"error": str(e)}

    # ② 달러 인덱스(DXY) 반영 자산가치 분석
    try:
        dxy_s   = _get_close("DX-Y.NYB", "1y")
        kospi_s = _get_close("^KS11",    "1y")

        if dxy_s is not None and kospi_s is not None:
            dxy_r  = dxy_s.pct_change().dropna()
            ksp_r  = kospi_s.reindex(dxy_s.index, method="ffill").pct_change().dropna()
            common = dxy_r.index.intersection(ksp_r.index)

            corr = _safe(dxy_r[common].corr(ksp_r[common])) if len(common) > 5 else None

            dxy_cur    = _safe(dxy_s.iloc[-1])
            dxy_1y_chg = None
            if dxy_cur and _safe(dxy_s.iloc[0]):
                dxy_1y_chg = round((dxy_cur / float(dxy_s.iloc[0]) - 1) * 100, 2)

            result["dxy_analysis"] = {
                "dxy_current":    round(dxy_cur, 2) if dxy_cur else None,
                "dxy_1y_change":  dxy_1y_chg,
                "kospi_dxy_corr": round(corr, 4) if corr else None,
                "interpretation": (
                    "음수(-): 달러 강세 시 코스피 하락 경향"
                    if corr and corr < 0
                    else "양수(+): 달러와 코스피 동반 상승"
                ),
                "description": "달러 인덱스와 코스피의 상관관계 분석",
            }
        else:
            result["dxy_analysis"] = {"error": "yfinance 데이터 없음"}
    except Exception as e:
        result["dxy_analysis"] = {"error": str(e)}

    # ③ 반도체 2종목 제외 코스피 기여도 분해
    try:
        syms = {
            "kospi":   "^KS11",
            "samsung": "005930.KS",
            "skhynix": "000660.KS",
        }
        data = {}
        for key, sym in syms.items():
            s = _get_close(sym, "3mo")
            if s is not None:
                ret = _pct_return(s)
                if ret is not None:
                    data[key] = {"return_pct": ret}

        kospi_r = data.get("kospi",   {}).get("return_pct")
        sam_r   = data.get("samsung", {}).get("return_pct")
        hyn_r   = data.get("skhynix", {}).get("return_pct")

        if kospi_r is not None:
            semicon = round(
                (sam_r or 0) * 0.18 + (hyn_r or 0) * 0.10, 2
            )
            others = round(kospi_r - semicon, 2)
            ratio  = round(abs(semicon / kospi_r * 100), 1) if kospi_r != 0 else 0

            result["semiconductor_skew"] = {
                "kospi_return":         round(kospi_r, 2),
                "samsung_return":       round(sam_r,   2) if sam_r is not None else 0,
                "skhynix_return":       round(hyn_r,   2) if hyn_r is not None else 0,
                "semicon_contribution": semicon,
                "others_contribution":  others,
                "semicon_ratio_pct":    ratio,
                "period":               "최근 3개월",
                "description":          "반도체 2종목이 코스피 상승에 기여한 비중",
            }
        else:
            result["semiconductor_skew"] = {"error": "코스피 데이터 없음"}
    except Exception as e:
        result["semiconductor_skew"] = {"error": str(e)}

    # ④ 부동산 자금 유입 효과 (정적 데이터)
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

    # ⑤ 개인 vs 기관 vs 외국인 수익률 비교 (정적 데이터)
    result["investor_returns"] = {
        "description": "투자자 유형별 연간 수익률 비교 (한국거래소·금융감독원 공개 데이터 기반)",
        "data": [
            {"year": 2020, "individual":  43.2, "institutional": 18.7, "foreign":  7.8},
            {"year": 2021, "individual":  -8.4, "institutional":  5.2, "foreign": 12.3},
            {"year": 2022, "individual": -28.1, "institutional": -19.4,"foreign":-22.6},
            {"year": 2023, "individual":  12.4, "institutional": 21.8, "foreign": 19.2},
            {"year": 2024, "individual":  -5.2, "institutional":  3.1, "foreign":  8.7},
        ],
        "insight": "개인 투자자는 변동성이 크고 장기적으로 기관·외국인 대비 수익률이 낮은 경향이 있습니다.",
    }

    return jsonify({"ok": True, "data": result})

@macro_bp.get("/debug")
def macro_debug():
    """각 심볼별 yfinance 성공/실패 진단"""
    import time

    symbols = {
        "KOSPI (^KS11)":     "^KS11",
        "KOSDAQ (^KQ11)":    "^KQ11",
        "S&P500 (^GSPC)":    "^GSPC",
        "NASDAQ (^IXIC)":    "^IXIC",
        "USDKRW (KRW=X)":    "KRW=X",
        "DXY (DX-Y.NYB)":    "DX-Y.NYB",
        "US10Y (^TNX)":      "^TNX",
        "GOLD (GC=F)":       "GC=F",
        "WTI (CL=F)":        "CL=F",
        "삼성전자 (005930.KS)": "005930.KS",
        "AAPL":              "AAPL",
    }

    results = {}
    for name, sym in symbols.items():
        start = time.time()
        try:
            hist = yf.Ticker(sym).history(period="5d")
            elapsed = round(time.time() - start, 2)
            if hist.empty:
                results[name] = {"status": "empty", "elapsed_sec": elapsed}
            else:
                results[name] = {"status": "ok", "rows": len(hist), "elapsed_sec": elapsed}
        except Exception as e:
            elapsed = round(time.time() - start, 2)
            results[name] = {"status": "error", "error": str(e)[:200], "elapsed_sec": elapsed}

    return jsonify({"ok": True, "results": results})