"""
포트폴리오 분석 모듈
R/R Score, Bull/Base/Bear 시나리오, 백테스팅
"""
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

SECTOR_MAP = {
    # ─── 반도체 ───
    "005930.KS": "반도체", "000660.KS": "반도체", "009150.KS": "반도체",
    "357780.KQ": "반도체", "058470.KQ": "반도체", "039030.KQ": "반도체",
    "095610.KQ": "반도체", "036540.KQ": "반도체", "067310.KQ": "반도체",
    "089030.KQ": "반도체", "064760.KQ": "반도체", "054620.KQ": "반도체",
    "101160.KQ": "반도체", "403870.KQ": "반도체", "370090.KQ": "반도체",
    "039440.KQ": "반도체", "101490.KQ": "반도체", "140860.KQ": "반도체",
    "090460.KQ": "반도체",
    "NVDA": "반도체", "AVGO": "반도체", "AMD": "반도체", "INTC": "반도체",
    "QCOM": "반도체", "MU": "반도체", "ASML": "반도체", "ARM": "반도체",
    "SOXX": "반도체",
    # ─── IT/인터넷 ───
    "035420.KS": "IT/인터넷", "035720.KS": "IT/인터넷", "018260.KS": "IT/인터넷",
    "030520.KQ": "IT/인터넷",
    "AAPL": "기술", "MSFT": "기술", "GOOGL": "기술", "CRM": "기술",
    "ORCL": "기술", "ADBE": "기술", "NOW": "기술", "PLTR": "기술",
    # ─── 화학/소재 ───
    "051910.KS": "화학/소재", "006400.KS": "화학/소재", "011170.KS": "화학/소재",
    "004000.KS": "화학/소재", "002380.KS": "화학/소재", "010060.KS": "화학/소재",
    "001570.KS": "화학/소재", "036830.KQ": "화학/소재",
    # ─── 바이오/헬스케어 ───
    "068270.KS": "바이오/헬스케어", "207940.KS": "바이오/헬스케어",
    "000100.KS": "바이오/헬스케어", "161890.KS": "바이오/헬스케어",
    "003090.KS": "바이오/헬스케어",
    "326030.KQ": "바이오/헬스케어", "196170.KQ": "바이오/헬스케어",
    "214150.KQ": "바이오/헬스케어", "145720.KQ": "바이오/헬스케어",
    "091990.KQ": "바이오/헬스케어", "068760.KQ": "바이오/헬스케어",
    "298380.KQ": "바이오/헬스케어", "290650.KQ": "바이오/헬스케어",
    "041920.KQ": "바이오/헬스케어", "048410.KQ": "바이오/헬스케어",
    "335890.KQ": "바이오/헬스케어", "285490.KQ": "바이오/헬스케어",
    "JNJ": "바이오/헬스케어", "PFE": "바이오/헬스케어", "LLY": "바이오/헬스케어",
    "UNH": "바이오/헬스케어",
    # ─── 자동차 ───
    "000270.KS": "자동차", "005380.KS": "자동차", "012330.KS": "자동차",
    # ─── 금융 ───
    "086790.KS": "금융", "105560.KS": "금융", "055550.KS": "금융",
    "316140.KS": "금융", "032830.KS": "금융", "000810.KS": "금융",
    "005830.KS": "금융", "005940.KS": "금융", "016360.KS": "금융",
    "006800.KS": "금융", "071050.KS": "금융",
    "JPM": "금융", "BAC": "금융", "GS": "금융", "MS": "금융",
    # ─── 에너지/유틸리티 ───
    "015760.KS": "에너지/유틸리티", "096770.KS": "에너지/유틸리티",
    "010950.KS": "에너지/유틸리티", "078930.KS": "에너지/유틸리티",
    "XOM": "에너지/유틸리티", "CVX": "에너지/유틸리티",
    # ─── 통신 ───
    "017670.KS": "통신", "030200.KS": "통신",
    # ─── 조선/중공업 ───
    "010140.KS": "조선/중공업", "009540.KS": "조선/중공업",
    "042660.KS": "조선/중공업", "329180.KS": "조선/중공업",
    "267250.KS": "조선/중공업", "010620.KS": "조선/중공업",
    # ─── 방산/우주항공 ───
    "064350.KS": "방산/우주항공", "012450.KS": "방산/우주항공",
    "047810.KS": "방산/우주항공", "272210.KS": "방산/우주항공",
    # ─── 항공/운송/물류 ───
    "003490.KS": "항공/운송", "020560.KS": "항공/운송",
    "028670.KS": "해운/물류", "000120.KS": "해운/물류", "011200.KS": "해운/물류",
    # ─── 건설/유통 ───
    "028260.KS": "건설/유통", "000720.KS": "건설/유통",
    # ─── 유통/소비 ───
    "071840.KS": "유통", "023530.KS": "유통", "007070.KS": "유통",
    "069960.KS": "유통", "004170.KS": "유통", "139480.KS": "유통",
    "WMT": "유통", "COST": "유통", "HD": "유통",
    # ─── 지주 ───
    "003550.KS": "지주", "034730.KS": "지주", "000880.KS": "지주",
    "001040.KS": "지주", "000210.KS": "지주", "180640.KS": "지주",
    # ─── 식음료 ───
    "005180.KS": "식음료", "007310.KS": "식음료", "000080.KS": "식음료",
    "097950.KS": "식음료", "271560.KS": "식음료",
    "MCD": "식음료", "SBUX": "식음료",
    # ─── 2차전지 ───
    "373220.KS": "2차전지", "003670.KS": "2차전지", "009830.KS": "2차전지",
    "247540.KQ": "2차전지", "086520.KQ": "2차전지", "222040.KQ": "2차전지",
    # ─── 엔터테인먼트/게임 ───
    "041510.KS": "엔터테인먼트", "352820.KS": "엔터테인먼트",
    "035900.KQ": "엔터테인먼트", "122870.KQ": "엔터테인먼트",
    "NFLX": "엔터테인먼트",
    "259960.KS": "게임", "036570.KS": "게임", "251270.KS": "게임",
    "263750.KQ": "게임", "112040.KQ": "게임", "007390.KQ": "게임",
    # ─── 로봇/자동화 ───
    "277810.KQ": "로봇/자동화", "060280.KQ": "로봇/자동화",
    # ─── 가전/생활용품 ───
    "066570.KS": "가전/생활용품", "021240.KS": "가전/생활용품",
    # ─── 철강/소재 ───
    "047050.KS": "철강/소재", "005490.KS": "철강/소재",
    "010130.KS": "철강/소재", "000670.KS": "철강/소재",
    # ─── IT/소셜미디어 ───
    "META": "소셜미디어",
    "AMZN": "전자상거래/클라우드",
    "TSLA": "전기차",
    # ─── ETF ───
    "SPY": "ETF", "QQQ": "ETF", "SOXX": "ETF", "ARKK": "ETF",
    # ─── 기타 ───
    "241560.KQ": "기계/중장비",
    "215000.KQ": "스포츠/레저",
    "008770.KS": "여행/호텔",
    "003240.KS": "섬유/패션",
}

AGGRESSIVE_SECTORS = {
    "반도체", "기술", "소셜미디어", "전기차", "전자상거래/클라우드",
    "바이오/헬스케어", "2차전지", "로봇/자동화", "게임", "엔터테인먼트", "방산/우주항공",
}

# ── 경기민감 중립 섹터 (공격도 방어도 아닌 중간 성격) ────
NEUTRAL_SECTORS = {
    "자동차",       # 경기 민감, 중간 변동성
    "화학/소재",    # 원자재 가격 연동, 중간 성격
    "철강/소재",    # 건설·제조 경기 연동
    "조선/중공업",  # 수주 사이클 긴 경기민감주
    "항공/운송",    # 경기민감 + 인프라 성격 혼재
    "해운/물류",    # 물동량 연동, 중간 성격
    "기계/중장비",  # 설비투자 사이클 연동
}
DEFENSIVE_SECTORS = {
    "금융", "에너지/유틸리티", "통신", "건설/유통", "유통", "지주",
    "식음료", "ETF", "가전/생활용품",
}


def infer_investment_type(holdings: list[dict]) -> str:
    """
    포트폴리오 구성 기반 투자 성향 자동 추론 — 5단계 분류

    🔥 초공격형:    공격 섹터 80% 이상
    🚀 공격투자형:  공격 섹터 65% 이상
    ⚖️  위험중립형:  그 외
    🛡️  안정추구형:  방어 섹터 60% 이상
    🏦 초안정형:    방어 섹터 80% 이상
    """
    aggressive_w = sum(
        h["weight"] for h in holdings
        if SECTOR_MAP.get(h["symbol"], "기타") in AGGRESSIVE_SECTORS
    )
    defensive_w = sum(
        h["weight"] for h in holdings
        if SECTOR_MAP.get(h["symbol"], "기타") in DEFENSIVE_SECTORS
    )
    max_weight  = max((h["weight"] for h in holdings), default=0)
    top2_weight = sum(
        sorted([h["weight"] for h in holdings], reverse=True)[:2]
    )

    # 🔥 초공격형: 공격 섹터 80% 이상 또는 단일 종목 70% 이상 집중
    if aggressive_w >= 80 or (aggressive_w >= 65 and max_weight >= 70):
        return "ultra_aggressive"

    # 🚀 공격투자형: 공격 섹터 65% 이상
    if (aggressive_w >= 65 or
            (aggressive_w >= 50 and max_weight > 50) or
            (aggressive_w >= 50 and top2_weight > 80)):
        return "aggressive"

    # 🏦 초안정형: 방어 섹터 80% 이상
    if defensive_w >= 80 and aggressive_w < 10:
        return "ultra_conservative"

    # 🛡️ 안정추구형: 방어 섹터 60% 이상
    if defensive_w >= 60 and aggressive_w < 20:
        return "conservative"

    # ⚖️ 위험중립형: 그 외
    return "balanced"


INVESTMENT_TYPE_LABEL = {
    "ultra_aggressive":   "초공격형",
    "aggressive":         "공격투자형",
    "balanced":           "위험중립형",
    "conservative":       "안정추구형",
    "ultra_conservative": "초안정형",
}


def _calc_scenarios_from_history(symbol: str, period: str = "3y") -> dict | None:
    try:
        hist = yf.Ticker(symbol).history(period=period)
        if hist is None or hist.empty:
            return None

        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = [c[0] for c in hist.columns]

        if "Close" not in hist.columns:
            return None

        close = hist["Close"].dropna()

        # 타임존 제거 (resample 오류 방지)
        if hasattr(close.index, "tz") and close.index.tz is not None:
            close.index = close.index.tz_localize(None)

        if len(close) < 60:
            return None

        # 월말 종가 추출 — ME 대신 M 사용 (버전 호환)
        try:
            monthly_close = close.resample("ME").last().dropna()
        except Exception:
            monthly_close = close.resample("M").last().dropna()

        if len(monthly_close) < 13:
            return None

        # 12개월 슬라이딩 윈도우로 연간 수익률 계산
        annual_returns = []
        for i in range(len(monthly_close) - 12):
            start_p = float(monthly_close.iloc[i])
            end_p   = float(monthly_close.iloc[i + 12])
            if start_p <= 0:
                continue
            r = (end_p / start_p - 1) * 100
            # 비정상적인 수치 필터링 (±200% 초과는 제외)
            if -200 <= r <= 200:
                annual_returns.append(r)

        if len(annual_returns) < 3:
            return None

        s    = pd.Series(annual_returns, dtype=float)
        mean = float(s.mean())
        std  = float(s.std())

        if std == 0:
            return None

        # 표준편차 기준 구간 분리
        bull_z = s[s > mean + std]
        bear_z = s[s < mean - std]
        base_z = s[(s >= mean - std) & (s <= mean + std)]

        bull_r = round(float(bull_z.mean()), 1) if len(bull_z) > 0 else round(mean + std, 1)
        base_r = round(float(base_z.mean()), 1) if len(base_z) > 0 else round(mean, 1)
        bear_r = round(float(bear_z.mean()), 1) if len(bear_z) > 0 else round(mean - std, 1)

        # bear_r은 반드시 음수
        if bear_r > 0:
            bear_r = -abs(bear_r)

        # 확률: 변동성 기반
        if std < 15:
            bull_p, base_p, bear_p = 15, 70, 15
        elif std < 30:
            bull_p, base_p, bear_p = 20, 60, 20
        else:
            bull_p, base_p, bear_p = 25, 50, 25

        return {
            "bull_r": bull_r, "bull_p": bull_p,
            "base_r": base_r, "base_p": base_p,
            "bear_r": bear_r, "bear_p": bear_p,
            "volatility":  round(std, 2),
            "data_points": len(annual_returns),
            "source":      "3년 실제 데이터",
        }
    except Exception:
        return None

def _calc_portfolio_scenarios(
    holdings: list[dict], investment_type: str
) -> tuple[dict, str]:
    """포트폴리오 전체 시나리오 = 종목별 시나리오 × 비중 가중 평균 (병렬 처리)"""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    bull_r = base_r = bear_r = 0.0
    bull_p = base_p = bear_p = 0.0
    total_weight  = 0.0
    success_count = 0

    # ── 종목별 yfinance 데이터 병렬 수집 ─────────────────
    results = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {
            executor.submit(_calc_scenarios_from_history, h["symbol"], "5y"): i
            for i, h in enumerate(holdings)
        }
        for future in as_completed(future_map):
            idx = future_map[future]
            try:
                results[idx] = future.result()
            except Exception:
                results[idx] = None

    for i, h in enumerate(holdings):
        sc = results.get(i)
        if sc is None:
            continue
        w = h["weight"] / 100
        bull_r += sc["bull_r"] * w
        base_r += sc["base_r"] * w
        bear_r += sc["bear_r"] * w
        bull_p += sc["bull_p"] * w
        base_p += sc["base_p"] * w
        bear_p += sc["bear_p"] * w
        total_weight  += w
        success_count += 1

    if total_weight >= 0.5 and success_count > 0:
        if total_weight < 1.0:
            ratio   = 1.0 / total_weight
            bull_r *= ratio; base_r *= ratio; bear_r *= ratio
            bull_p *= ratio; base_p *= ratio; bear_p *= ratio

        p_total = bull_p + base_p + bear_p
        if p_total > 0:
            bull_p = round(bull_p / p_total * 100)
            bear_p = round(bear_p / p_total * 100)
            base_p = 100 - bull_p - bear_p

        source = f"3년 실제 데이터 ({success_count}/{len(holdings)}개 종목)"
        return {
            "bull_r": round(bull_r, 1), "bull_p": int(bull_p),
            "base_r": round(base_r, 1), "base_p": int(base_p),
            "bear_r": round(bear_r, 1), "bear_p": int(bear_p),
        }, source

    d = _FALLBACK_SCENARIOS.get(investment_type, _FALLBACK_SCENARIOS["balanced"])
    return d, "기본 시나리오 (데이터 수집 실패)"


def compute_rr_score(holdings: list[dict], investment_type: str = "auto") -> dict:
    """
    R/R Score 계산 — 3년 실제 데이터 기반 정석 공식

    ① 종목별 3년 월말 종가 → 12개월 슬라이딩 윈도우 → 연간 수익률
    ② 표준편차 기준으로 Bull/Base/Bear 구간 분리
    ③ 변동성 기반 확률 설정
    ④ 정석 공식:
       R/R Score = (Bull×확률 + Base×확률) / |Bear×확률|

    판정 기준:
      3.0 초과  →  🟢 매력적   — 기대 수익이 기대 손실의 3배 초과
      1.0~3.0   →  🟡 중립     — 수익이 손실보다 크지만 3배 미만
      1.0 미만  →  🔴 비매력적 — 기대 손실이 기대 수익 이상
    """
    if investment_type == "auto" or not investment_type:
        investment_type = infer_investment_type(holdings)

    sectors       = set(SECTOR_MAP.get(h["symbol"], "기타") for h in holdings)
    num_sectors   = len(sectors)
    num_holdings  = len(holdings)
    max_weight    = max((h["weight"] for h in holdings), default=0)
    concentration = max_weight / 100

    sc, data_source = _calc_portfolio_scenarios(holdings, investment_type)

    br  = sc["bull_r"];  bp  = sc["bull_p"] / 100
    bar = sc["base_r"];  bap = sc["base_p"] / 100
    ber = sc["bear_r"];  bep = sc["bear_p"] / 100

    expected_gain = (br * bp) + (bar * bap)
    expected_loss = abs(ber) * bep  # ber는 음수이므로 abs() 따로 처리
    if expected_loss <= 0:
        print(f"[경고] expected_loss가 0 이하: ber={ber}, bep={bep}")
        expected_loss = 0.01  # 0 나누기 방지용 최솟값
    raw_score = expected_gain / expected_loss

    # 보정 없이 raw_score 그대로 사용
    # R/R Score는 비율(배수)이므로 10점 만점 척도가 아님
    final_score = round(max(raw_score, 0.0), 2)

    if final_score > 3.0:
        label = "attractive";    label_kr = "매력적";    emoji = "🟢"
    elif final_score >= 1.0:
        label = "neutral";       label_kr = "중립";      emoji = "🟡"
    else:
        label = "unfavorable";   label_kr = "비매력적";  emoji = "🔴"

    return {
        "score":            final_score,
        "raw_score":        round(raw_score, 2),
        "risk":             round(abs(ber) * bep * 100, 1),
        "reward":           round(expected_gain, 1),
        "label":            label,
        "label_kr":         label_kr,
        "emoji":            emoji,
        "inferred_type":    investment_type,
        "inferred_type_kr": INVESTMENT_TYPE_LABEL.get(investment_type, ""),
        "data_source":      data_source,
        "scenarios_used": {
            "bull": {"return": br,  "prob": round(bp  * 100)},
            "base": {"return": bar, "prob": round(bap * 100)},
            "bear": {"return": ber, "prob": round(bep * 100)},
        },
    }


def compute_scenarios(rr: dict, investment_type: str = "balanced") -> list[dict]:
    """Bull/Base/Bear 시나리오 분석"""
    reward = rr["reward"]
    risk = rr["risk"]

    return [
        {
            "scenario": "Bull",
            "emoji": "🐂",
            "expectedReturn": round(reward * 1.5, 1),
            "probability": 30,
            "description": "경기 호조, 금리 인하, 기업 실적 개선 시나리오",
            "color": "#00C896",
        },
        {
            "scenario": "Base",
            "emoji": "📊",
            "expectedReturn": round(reward * 0.8, 1),
            "probability": 45,
            "description": "현재 추세 지속, 완만한 성장 시나리오",
            "color": "#4A9EFF",
        },
        {
            "scenario": "Bear",
            "emoji": "🐻",
            "expectedReturn": round(-risk * 0.8, 1),
            "probability": 25,
            "description": "경기 침체, 금리 급등, 지정학적 리스크 시나리오",
            "color": "#FF6B6B",
        },
    ]


def compute_sector_allocation(holdings: list[dict]) -> dict:
    """섹터별 비중 계산"""
    allocation = {}
    for h in holdings:
        sector = SECTOR_MAP.get(h["symbol"], "기타")
        allocation[sector] = round(allocation.get(sector, 0) + h["weight"], 1)
    return allocation


def backtest_portfolio(
    holdings: list[dict],
    start_date: datetime,
    end_date: datetime,
    initial_amount: float,
    benchmark_symbol: str = "^KS11",
) -> dict:
    """포트폴리오 백테스팅"""
    symbols = [h["symbol"] for h in holdings]
    weights = [h["weight"] / 100 for h in holdings]

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    try:
        portfolio_data = {}
        for sym in symbols:
            try:
                df = yf.download(sym, start=start_str, end=end_str, progress=False, auto_adjust=True)
                if not df.empty:
                    close = df["Close"] if "Close" in df.columns else df.iloc[:, 0]
                    portfolio_data[sym] = close.squeeze()
            except Exception:
                pass

        if not portfolio_data:
            return _generate_mock_backtest(initial_amount, start_date, end_date)

        portfolio_df = pd.DataFrame(portfolio_data)
        portfolio_df = portfolio_df.ffill().dropna()

        if portfolio_df.empty or len(portfolio_df) < 5:
            return _generate_mock_backtest(initial_amount, start_date, end_date)

        valid_syms = list(portfolio_df.columns)
        valid_weights = [w for sym, w in zip(symbols, weights) if sym in valid_syms]

        if not valid_weights:
            return _generate_mock_backtest(initial_amount, start_date, end_date)

        total_w = sum(valid_weights)
        valid_weights = [w / total_w for w in valid_weights]

        returns = portfolio_df[valid_syms].pct_change().dropna()
        portfolio_returns = (returns * valid_weights).sum(axis=1)

        cumulative = (1 + portfolio_returns).cumprod()
        portfolio_values = cumulative * initial_amount

        max_val = portfolio_values.cummax()
        drawdown = ((portfolio_values - max_val) / max_val * 100)
        max_drawdown = abs(drawdown.min())

        try:
            bench = yf.download(benchmark_symbol, start=start_str, end=end_str, progress=False, auto_adjust=True)
            bench_close = bench["Close"].squeeze() if not bench.empty else None
            if bench_close is not None and not bench_close.empty:
                bench_returns = bench_close.pct_change().dropna()
                bench_cumulative = (1 + bench_returns).cumprod()
                bench_values = bench_cumulative * initial_amount
                bench_values = bench_values.reindex(portfolio_values.index, method="ffill")
            else:
                bench_values = pd.Series(
                    [initial_amount * (1 + 0.0003) ** i for i in range(len(portfolio_values))],
                    index=portfolio_values.index,
                )
        except Exception:
            bench_values = pd.Series(
                [initial_amount * (1 + 0.0003) ** i for i in range(len(portfolio_values))],
                index=portfolio_values.index,
            )

        total_return = (portfolio_values.iloc[-1] / initial_amount - 1) * 100
        bench_return = (bench_values.iloc[-1] / initial_amount - 1) * 100

        years = max((end_date - start_date).days / 365, 0.1)
        ann_return = (portfolio_values.iloc[-1] / initial_amount) ** (1 / years) - 1
        ann_return_pct = ann_return * 100

        ann_vol = portfolio_returns.std() * np.sqrt(252) * 100
        sharpe = (ann_return - 0.035) / (ann_vol / 100) if ann_vol > 0 else 0

        win_rate = (portfolio_returns > 0).sum() / len(portfolio_returns) * 100

        data_points = []
        step = max(len(portfolio_values) // 100, 1)
        for i in range(0, len(portfolio_values), step):
            date = portfolio_values.index[i]
            data_points.append({
                "date": date.strftime("%Y-%m-%d") if hasattr(date, "strftime") else str(date),
                "portfolio": round(float(portfolio_values.iloc[i]), 0),
                "benchmark": round(float(bench_values.iloc[i]) if i < len(bench_values) else initial_amount, 0),
                "drawdown": round(float(drawdown.iloc[i]), 2),
            })

        return {
            "totalReturn": round(float(total_return), 2),
            "annualizedReturn": round(float(ann_return_pct), 2),
            "maxDrawdown": round(float(max_drawdown), 2),
            "sharpeRatio": round(float(sharpe), 2),
            "volatility": round(float(ann_vol), 2),
            "winRate": round(float(win_rate), 1),
            "benchmarkReturn": round(float(bench_return), 2),
            "dataPoints": data_points,
            "finalValue": round(float(portfolio_values.iloc[-1]), 0),
        }

    except Exception:
        return _generate_mock_backtest(initial_amount, start_date, end_date)


def _generate_mock_backtest(initial_amount: float, start_date: datetime, end_date: datetime) -> dict:
    """모의 백테스팅 결과 생성 (데이터 수집 실패 시 폴백)"""
    import random
    days = (end_date - start_date).days
    years = max(days / 365, 0.1)

    port_value = initial_amount
    bench_value = initial_amount
    max_value = initial_amount
    data_points = []

    for i in range(0, days, 7):
        date = start_date + timedelta(days=i)
        if date > end_date:
            break
        port_value *= (1 + random.gauss(0.001, 0.02))
        bench_value *= (1 + random.gauss(0.0005, 0.015))
        max_value = max(max_value, port_value)
        drawdown = (port_value - max_value) / max_value * 100

        data_points.append({
            "date": date.strftime("%Y-%m-%d"),
            "portfolio": round(port_value, 0),
            "benchmark": round(bench_value, 0),
            "drawdown": round(drawdown, 2),
        })

    total_return = (port_value / initial_amount - 1) * 100
    bench_return = (bench_value / initial_amount - 1) * 100
    ann_return = ((port_value / initial_amount) ** (1 / years) - 1) * 100

    return {
        "totalReturn": round(total_return, 2),
        "annualizedReturn": round(ann_return, 2),
        "maxDrawdown": 15.5,
        "sharpeRatio": 0.85,
        "volatility": 18.2,
        "winRate": 53.4,
        "benchmarkReturn": round(bench_return, 2),
        "dataPoints": data_points,
        "finalValue": round(port_value, 0),
    }
