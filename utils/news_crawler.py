"""
뉴스 크롤링 모듈 - 네이버 금융 기반 뉴스 수집
감성 분석: CLOVA Studio API (기사 원문 분석) + KNU 폴백
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import time
import json, os, re

# ── User-Agent 풀 (크롤링 차단 방지) ─────────────────────
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
]

def _random_ua() -> dict:
    return {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept-Language": "ko-KR,ko;q=0.9",
    }

POSITIVE_WORDS = [
    "상승", "급등", "호실적", "증가", "선점", "수혜", "성장", "양산", "회복",
    "외국인매수", "목표가상향", "기대", "돌파", "신고가", "흑자", "강세",
    "호재", "수주", "계약", "협력", "투자", "확장", "개선", "최대",
]
NEGATIVE_WORDS = [
    "하락", "급락", "우려", "감소", "이탈", "수율문제", "부진", "약세",
    "리스크", "위기", "손실", "적자", "폭락", "경고", "악재", "실망",
    "하향", "부정", "침체", "위축", "둔화", "불확실",
]

# ── KNU 감성사전 로드 ─────────────────────────────────────
_KNU_DICT = {}
_KNU_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "SentiWord_Dict.txt"
)
try:
    with open(_KNU_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "\t" not in line:
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                word  = parts[0].strip()
                score = float(parts[1].strip())
                _KNU_DICT[word] = score
    print(f"[KNU] 감성사전 로드 완료: {len(_KNU_DICT)}개 단어")
except FileNotFoundError:
    print("[KNU] 감성사전 파일 없음 → 기존 방식으로 동작")
except Exception as e:
    print(f"[KNU] 로드 실패: {e}")

# ── 금융 도메인 특화 보정 가중치 ─────────────────────────
FINANCE_ADJUST = {
    "폭등":    -1.0,
    "급등":    -0.5,
    "강세":    +0.5,
    "확대":    -0.5,
    "반등":    +1.5,
    "저점":    +0.5,
    "어닝쇼크":      -2.0,
    "어닝서프라이즈": +2.0,
    "신고가":        +2.0,
    "신저가":        -2.0,
    "목표가상향":     +1.5,
    "목표가하향":     -1.5,
    "투자의견매수":   +2.0,
    "투자의견매도":   -2.0,
    "흑자전환":      +2.0,
    "적자전환":      -2.0,
    "자사주매입":     +1.0,
    "유상증자":      -1.0,
    "실적쇼크":      -2.0,
    "깜짝실적":      +2.0,
}

# ── 부정 컨텍스트 패턴 (문맥 오류 보정) ──────────────────
# "환율 폭등"처럼 앞 단어에 따라 부정이 되는 패턴
NEGATIVE_CONTEXT = {
    "환율":  ["폭등", "급등", "상승", "강세"],
    "금리":  ["폭등", "급등", "인상", "상승"],
    "물가":  ["폭등", "급등", "상승"],
    "부채":  ["증가", "확대", "급증"],
    "적자":  ["확대", "증가", "급증"],
    "실업":  ["증가", "확대", "급증"],
    "원달러": ["상승", "급등", "폭등"],
}

# ── 신뢰 언론사 화이트리스트 ─────────────────────────────
TRUSTED_PRESS = {
    "한국경제", "매일경제", "서울경제", "파이낸셜뉴스",
    "머니투데이", "이데일리", "헤럴드경제", "아시아경제",
    "비즈니스포스트", "더벨", "인베스트조선",
    "연합뉴스", "연합인포맥스", "뉴스1", "뉴시스",
    "조선비즈", "중앙일보", "동아일보", "한겨레",
    "한국경제TV", "연합뉴스TV",
}

# ── CLOVA Studio API 설정 ────────────────────────────────
_CLOVA_API_KEY = os.environ.get("CLOVA_API_KEY", "")
_CLOVA_API_URL = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"

# ── 네이버 금융 종목 코드 맵 ──────────────────────────────
NAVER_STOCK_CODE_MAP = {
    "005930.KS": "005930", "000660.KS": "000660", "035420.KS": "035420",
    "051910.KS": "051910", "006400.KS": "006400", "035720.KS": "035720",
    "068270.KS": "068270", "207940.KS": "207940", "000270.KS": "000270",
    "005380.KS": "005380", "012330.KS": "012330", "096770.KS": "096770",
    "034730.KS": "034730", "028260.KS": "028260", "066570.KS": "066570",
    "003550.KS": "003550", "015760.KS": "015760", "017670.KS": "017670",
    "030200.KS": "030200", "086790.KS": "086790", "105560.KS": "105560",
    "055550.KS": "055550", "316140.KS": "316140", "032830.KS": "032830",
    "018260.KS": "018260", "009150.KS": "009150", "011200.KS": "011200",
    "047050.KS": "047050", "000100.KS": "000100", "010130.KS": "010130",
    "009830.KS": "009830", "010950.KS": "010950", "078930.KS": "078930",
    "161890.KS": "161890", "000720.KS": "000720", "005490.KS": "005490",
    "373220.KS": "373220", "003670.KS": "003670", "041510.KS": "041510",
    "352820.KS": "352820", "259960.KS": "259960", "036570.KS": "036570",
    "251270.KS": "251270", "139480.KS": "139480", "097950.KS": "097950",
    "271560.KS": "271560", "008770.KS": "008770", "000080.KS": "000080",
    "021240.KS": "021240", "000810.KS": "000810", "005830.KS": "005830",
    "005940.KS": "005940", "016360.KS": "016360", "006800.KS": "006800",
    "071050.KS": "071050", "010140.KS": "010140", "009540.KS": "009540",
    "042660.KS": "042660", "329180.KS": "329180", "267250.KS": "267250",
    "010620.KS": "010620", "064350.KS": "064350", "012450.KS": "012450",
    "047810.KS": "047810", "272210.KS": "272210", "003490.KS": "003490",
    "020560.KS": "020560", "028670.KS": "028670", "000120.KS": "000120",
    "011170.KS": "011170", "004000.KS": "004000", "010060.KS": "010060",
    "002380.KS": "002380", "071840.KS": "071840", "023530.KS": "023530",
    "007070.KS": "007070", "069960.KS": "069960", "004170.KS": "004170",
    "000880.KS": "000880", "001040.KS": "001040", "000210.KS": "000210",
    "180640.KS": "180640", "005180.KS": "005180", "007310.KS": "007310",
    "277810.KQ": "277810", "326030.KQ": "326030", "263750.KQ": "263750",
    "357780.KQ": "357780", "247540.KQ": "247540", "086520.KQ": "086520",
    "196170.KQ": "196170", "214150.KQ": "214150", "112040.KQ": "112040",
    "058470.KQ": "058470", "145720.KQ": "145720", "035900.KQ": "035900",
    "122870.KQ": "122870", "091990.KQ": "091990", "068760.KQ": "068760",
    "039030.KQ": "039030", "095610.KQ": "095610", "403870.KQ": "403870",
    "036540.KQ": "036540", "067310.KQ": "067310", "089030.KQ": "089030",
    "064760.KQ": "064760", "054620.KQ": "054620", "101160.KQ": "101160",
    "298380.KQ": "298380", "060280.KQ": "060280", "140860.KQ": "140860",
    "335890.KQ": "335890", "285490.KQ": "285490", "215000.KQ": "215000",
    "030520.KQ": "030520", "036830.KQ": "036830", "241560.KQ": "241560",
    "370090.KQ": "370090", "090460.KQ": "090460", "007390.KQ": "007390",
}


# ── 감성 분석 함수들 ──────────────────────────────────────

def simple_sentiment_score(text: str) -> float:
    """단순 키워드 기반 감성 점수 계산"""
    pos = sum(1 for w in POSITIVE_WORDS if w in text)
    neg = sum(1 for w in NEGATIVE_WORDS if w in text)
    if pos + neg == 0:
        return 0.0
    return round((pos - neg) / (pos + neg), 2)


def hybrid_sentiment_score(text: str) -> float:
    """KNU + 금융 가중치 + 부정 컨텍스트 보정"""
    if not _KNU_DICT:
        score = simple_sentiment_score(text)
    else:
        score = 0.0
        matched_count = 0
        for word, polarity in _KNU_DICT.items():
            if word in text:
                score += polarity
                matched_count += 1
        for word, weight in FINANCE_ADJUST.items():
            if word in text:
                score += weight * 1.5
                matched_count += 1
        if matched_count == 0:
            score = simple_sentiment_score(text)
        else:
            score = score / matched_count

    # 부정 컨텍스트 패턴 보정
    for neg_noun, pos_words in NEGATIVE_CONTEXT.items():
        if neg_noun in text:
            for word in pos_words:
                if word in text:
                    score -= 1.5
                    break

    return round(max(-2.0, min(2.0, score)), 3)


def clova_sentiment_score(title: str, content: str = "") -> dict:
    """
    CLOVA Studio API로 기사 원문 감성 분석
    반환: {"score": float, "label": str, "reason": str, "grade": str}

    신뢰도 등급:
    A — CLOVA Studio 원문 + 제목 분석 성공
    B — 원문 수집 실패, 제목만 분석
    C — CLOVA API 실패, KNU 감성사전 사용
    D — 감성 분석 불가
    """
    if not _CLOVA_API_KEY:
        score = hybrid_sentiment_score(title)
        label = "positive" if score > 0.1 else "negative" if score < -0.1 else "neutral"
        return {"score": score, "label": label, "reason": "KNU 감성사전", "grade": "C"}

    # 원문 있으면 A등급, 없으면 B등급
    has_content = bool(content and len(content) > 30)
    grade_ok    = "A" if has_content else "B"

    text = f"제목: {title}"
    if has_content:
        text += f"\n본문: {content[:300]}"

    prompt = f"""다음 금융 뉴스를 주식 투자자 관점에서 분석하세요.

{text}

판단 기준:
- 실적 호조, 수주, 목표가 상향, 신사업, 주가 상승, 흑자전환 → 긍정 (0.5 ~ 2.0)
- 실적 부진, 손실, 리스크, 주가 하락, 적자, 위기, 우려 → 부정 (-0.5 ~ -2.0)
- 단순 사실 보도, 중립적 정보 → 중립 (-0.3 ~ 0.3)

반드시 아래 JSON 형식으로만 답하세요. 다른 말은 쓰지 마세요:
{{"score": -2.0에서 2.0 사이 숫자, "label": "positive" 또는 "negative" 또는 "neutral", "reason": "판단 이유 한 줄"}}"""

    try:
        resp = requests.post(
            _CLOVA_API_URL,
            headers={
                "Authorization": f"Bearer {_CLOVA_API_KEY}",
                "Content-Type":  "application/json",
            },
            json={
                "messages": [{"role": "user", "content": prompt}],
                "maxTokens":   200,
                "temperature": 0.1,
                "topP":        0.8,
            },
            timeout=10,
        )

        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}")

        data         = resp.json()
        content_text = (
            data.get("result", {})
                .get("message", {})
                .get("content", "")
        )

        match = re.search(r'\{[^}]+\}', content_text, re.DOTALL)
        if match:
            result = json.loads(match.group())
            score  = float(result.get("score", 0))
            score  = max(-2.0, min(2.0, score))
            raw_label = result.get("label", "neutral")
            reason    = result.get("reason", "")
            # CLOVA label 우선, score로 보완 (기준 0.1로 완화)
            if raw_label == "positive" or score > 0.1:
                label = "positive"
            elif raw_label == "negative" or score < -0.1:
                label = "negative"
            else:
                label = "neutral"
            return {"score": round(score, 3), "label": label, "reason": reason, "grade": grade_ok}

    except Exception as e:
        print(f"[CLOVA] 분석 실패: {e} → KNU 폴백")

    # 실패 시 KNU 폴백
    score = hybrid_sentiment_score(title)
    label = "positive" if score > 0.1 else "negative" if score < -0.1 else "neutral"
    return {"score": score, "label": label, "reason": "KNU 감성사전", "grade": "C"}


def crawl_article_content(url: str) -> str:
    """기사 원문 본문 크롤링 (500자 이내) — 재시도 포함"""

    # ── finance.naver.com URL → 모바일 뉴스 URL 변환 ──────
    import urllib.parse as _up
    if "finance.naver.com" in url:
        try:
            params     = _up.parse_qs(_up.urlparse(url).query)
            article_id = params.get("article_id", [""])[0]
            office_id  = params.get("office_id",  [""])[0]
            if article_id and office_id:
                url = f"https://n.news.naver.com/article/{office_id}/{article_id}"
                print(f"[크롤링] URL 변환 → {url}")
        except Exception:
            pass

    for attempt in range(2):
        try:
            resp = requests.get(url, headers=_random_ua(), timeout=5)
            resp.encoding = resp.apparent_encoding or "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            for tag in soup(["script", "style", "aside", "nav", "footer", "iframe"]):
                tag.decompose()

            for sel in [
                "div#newsct_article",
                "div.newsct_article",
                "div#articeBody",
                "div#article-body",
                "div.article-body",
                "div.article_body",
                "div#articleBody",
                "div#article_body",
                "div.article-content",
                "div#content-article",
                "div.news_content",
                "div.news-content",
                "div#newsContent",
                "section.article-section",
                "div.entry-content",
                "article",
                "div#content",
                "div.content",
                "div.post-content",
            ]:
                tag = soup.select_one(sel)
                if tag:
                    text = tag.get_text(separator=" ", strip=True)
                    if len(text) > 50:
                        print(f"[크롤링] ✅ 성공 ({sel}) {len(text)}자")
                        return text[:500]

            paragraphs = soup.select(
                "article p, .article p, .content p, "
                ".news_body p, .article-body p, #article p"
            )
            if paragraphs:
                text = " ".join(p.get_text(strip=True) for p in paragraphs[:8])
                if len(text) > 50:
                    print(f"[크롤링] ✅ 성공 (p태그) {len(text)}자")
                    return text[:500]

            body = soup.find("body")
            if body:
                text = body.get_text(separator=" ", strip=True)
                if len(text) > 100:
                    print(f"[크롤링] ⚠️ body폴백 {len(text)}자")
                    return text[:500]

            print(f"[크롤링] ❌ 실패 (선택자 없음) status={resp.status_code} — {url[:60]}")

        except Exception as e:
            print(f"[크롤링] ❌ 예외 ({e}) — {url[:60]}")
            if attempt == 0:
                time.sleep(0.5)
    return ""


def extract_keywords(text: str) -> list[str]:
    """텍스트에서 감성 키워드 추출"""
    kws = []
    for w in POSITIVE_WORDS + NEGATIVE_WORDS:
        if w in text and w not in kws:
            kws.append(w)
    return kws[:8]


def extract_original_url(naver_article_url: str) -> str | None:
    """네이버 기사 페이지에서 언론사 원문 URL 추출"""
    try:
        res = requests.get(naver_article_url, headers=_random_ua(), timeout=3)
        res.encoding = res.apparent_encoding or "euc-kr"
        soup = BeautifulSoup(res.text, "html.parser")

        for sel in [
            "a.media_end_head_origin_link",
            "a.link_origin",
            "a#originLink",
            "div.article_body a[href^='http']",
        ]:
            tag = soup.select_one(sel)
            if tag and tag.get("href", "").startswith("http"):
                href = tag["href"]
                if "naver.com" not in href:
                    return href

        og = soup.select_one('meta[property="og:url"]')
        if og and og.get("content", "").startswith("http"):
            content = og["content"]
            if "naver.com" not in content:
                return content

    except Exception:
        pass

    # 네이버 뉴스 URL이면 모바일 버전으로 변환 (본문 추출 용이)
    # https://news.naver.com/article/001/0001234 → 그대로 사용
    # n.news.naver.com 모바일 URL로 변환 시도
    try:
        import re as _re
        m = _re.search(r'article/(\d+)/(\d+)', naver_article_url)
        if m:
            oid, aid = m.group(1), m.group(2)
            return f"https://n.news.naver.com/article/{oid}/{aid}"
    except Exception:
        pass

    return None


def _is_trusted(source: str) -> bool:
    if not source:
        return True
    return any(press in source for press in TRUSTED_PRESS)


def _remove_exact_duplicates(news_list: list[dict]) -> list[dict]:
    seen = {}
    for news in news_list:
        raw_title  = news.get("title", "")
        normalized = "".join(
            c for c in raw_title
            if c.isalnum() or '\uAC00' <= c <= '\uD7A3'
        ).lower()
        if normalized not in seen:
            seen[normalized] = news
        else:
            existing = seen[normalized]
            if (_is_trusted(news.get("source", "")) and
                    not _is_trusted(existing.get("source", ""))):
                seen[normalized] = news
    return list(seen.values())


def _remove_similar_duplicates(
    news_list: list[dict], threshold: float = 0.7
) -> list[dict]:
    if not news_list:
        return []

    def jaccard(a: str, b: str) -> float:
        def bigrams(t):
            return set(t[i:i+2] for i in range(len(t) - 1))
        sa, sb = bigrams(a), bigrams(b)
        if not sa or not sb:
            return 0.0
        return len(sa & sb) / len(sa | sb)

    result, kept = [], []
    for news in sorted(news_list,
                       key=lambda x: 0 if _is_trusted(x.get("source","")) else 1):
        title  = news.get("title", "")
        is_dup = any(jaccard(title, k) >= threshold for k in kept)
        if not is_dup:
            result.append(news)
            kept.append(title)
    return result


def filter_quality_news(
    news_list: list[dict],
    use_trust_filter: bool = True,
    similarity_threshold: float = 0.7,
    max_age_days: int = 30,
) -> list[dict]:
    """
    뉴스 품질 필터 통합 함수
    1단계: 신뢰 언론사 필터
    2단계: 오래된 기사 제거 (max_age_days일 초과)
    3단계: 완전 동일 제목 제거
    4단계: 유사 제목 중복 제거
    """
    original_count = len(news_list)

    # 1단계: 신뢰 언론사 필터
    if use_trust_filter:
        trusted = [n for n in news_list if _is_trusted(n.get("source", ""))]
        if len(trusted) >= 3:
            news_list = trusted

    # 2단계: 오래된 기사 제거
    cutoff = datetime.now() - timedelta(days=max_age_days)
    filtered = []
    for n in news_list:
        date_str = n.get("date", "")
        try:
            # 네이버 날짜 형식: "2024.01.15 14:30" 또는 "01.15 14:30"
            if date_str:
                for fmt in ["%Y.%m.%d %H:%M", "%m.%d %H:%M", "%Y.%m.%d"]:
                    try:
                        parsed = datetime.strptime(date_str.strip(), fmt)
                        if fmt == "%m.%d %H:%M":
                            parsed = parsed.replace(year=datetime.now().year)
                        if parsed >= cutoff:
                            filtered.append(n)
                        break
                    except ValueError:
                        continue
                else:
                    filtered.append(n)  # 날짜 파싱 실패시 포함
            else:
                filtered.append(n)
        except Exception:
            filtered.append(n)
    news_list = filtered

    # 3단계: 완전 동일 제목 제거
    news_list = _remove_exact_duplicates(news_list)

    # 4단계: 유사 제목 중복 제거
    news_list = _remove_similar_duplicates(news_list, threshold=similarity_threshold)

    print(f"[필터] {original_count}건 → {len(news_list)}건 "
          f"({original_count - len(news_list)}건 제거)")

    return news_list


def _analyze_one(item: dict) -> dict:
    """
    단일 기사 원문 크롤링 + 감성 분석 (병렬 처리용)
    """
    url     = item.get("url", "")
    title   = item.get("title", "")
    content = crawl_article_content(url) if url else ""
    result  = clova_sentiment_score(title, content)
    item.update({
        "sentimentLabel":  result["label"],
        "sentimentScore":  result["score"],
        "sentimentReason": result.get("reason", ""),
        "grade":           result.get("grade", "🟡 KNU폴백"),
        "keywords":        extract_keywords(title),
    })
    return item


def crawl_naver_news(symbol: str, limit: int = 10) -> list[dict]:
    """
    1차: 네이버 금융 종목 뉴스 크롤링
    2차: 네이버 뉴스 검색 폴백 (해외 종목 포함)
    감성 분석: ThreadPoolExecutor 병렬 처리로 속도 개선
    """
    naver_code = NAVER_STOCK_CODE_MAP.get(symbol, "")
    raw_items  = []   # 감성 분석 전 기사 목록

    # ── 1차: 네이버 금융 종목 뉴스 ────────────────────────
    if naver_code:
        list_url = (
            f"https://finance.naver.com/item/news_news.naver"
            f"?code={naver_code}&page=1"
        )
        for attempt in range(2):
            try:
                resp = requests.get(
                    list_url,
                    headers={**_random_ua(), "Referer": "https://finance.naver.com"},
                    timeout=8,
                )
                resp.encoding = "euc-kr"
                soup = BeautifulSoup(resp.text, "html.parser")

                rows = (
                    soup.select("table.type5 tbody tr") or
                    soup.select("div.news_list li") or
                    soup.select("ul.news_list li")
                )

                collect_limit = limit * 2  # 수집 개수 축소로 속도 개선
                for row in rows:
                    if len(raw_items) >= collect_limit:
                        break

                    title_tag = (
                        row.select_one("td.title a") or
                        row.select_one("a.title") or
                        row.select_one("a")
                    )
                    if not title_tag:
                        continue

                    title = title_tag.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue

                    href      = title_tag.get("href", "")
                    naver_url = (
                        href if href.startswith("http")
                        else f"https://finance.naver.com{href}"
                    )
                    original_url = extract_original_url(naver_url)
                    final_url    = original_url if original_url else naver_url
                    if not final_url.startswith("http"):
                        continue

                    source_tag = (
                        row.select_one("td.info") or
                        row.select_one("span.press")
                    )
                    date_tag = (
                        row.select_one("td.date") or
                        row.select_one("span.date")
                    )

                    raw_items.append({
                        "title":      title,
                        "url":        final_url,
                        "source":     source_tag.get_text(strip=True) if source_tag else "네이버금융",
                        "date":       date_tag.get_text(strip=True)   if date_tag   else "",
                        "isOriginal": original_url is not None,
                    })
                break  # 성공하면 재시도 안 함

            except Exception as e:
                print(f"[1차 크롤링 실패 {attempt+1}/2] {symbol} → {e}")
                if attempt == 0:
                    time.sleep(1)

    # ── 2차: 검색 폴백 (1차 실패 또는 해외 종목) ──────────
    if not raw_items:
        raw_items = _collect_search_news(symbol, limit * 3)

    if not raw_items:
        print(f"[뉴스] {symbol} — 수집된 기사 없음")
        return []

    # ── 품질 필터 (감성 분석 전에 먼저 중복·오래된 기사 제거) ──
    raw_items = filter_quality_news(
        raw_items,
        use_trust_filter=True,
        similarity_threshold=0.7,
        max_age_days=30,
    )

    # ── 병렬 감성 분석 (ThreadPoolExecutor) ──────────────
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_analyze_one, item): item for item in raw_items}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                print(f"[감성분석 오류] {e}")

    return results[:limit * 2]


def _collect_search_news(symbol: str, limit: int) -> list[dict]:
    """
    네이버 공식 검색 API로 뉴스 수집
    해외 종목 한글명으로 검색
    """
    import os

    client_id     = os.getenv("NAVER_CLIENT_ID", "")
    client_secret = os.getenv("NAVER_CLIENT_SECRET", "")

    # 해외 종목 한글명 매핑
    OVERSEAS_KR = {
        "NVDA": "엔비디아", "AAPL": "애플", "MSFT": "마이크로소프트",
        "GOOGL": "구글", "GOOG": "구글", "AMZN": "아마존", "META": "메타",
        "TSLA": "테슬라", "AMD": "AMD", "INTC": "인텔", "AVGO": "브로드컴",
        "QCOM": "퀄컴", "MU": "마이크론", "NFLX": "넷플릭스",
        "CRM": "세일즈포스", "ORCL": "오라클", "NOW": "서비스나우",
        "ADBE": "어도비", "INTU": "인튜이트", "WDAY": "워크데이",
        "TEAM": "아틀라시안", "SNOW": "스노우플레이크", "DDOG": "데이터도그",
        "CRWD": "크라우드스트라이크", "PANW": "팔로알토", "ZS": "지스케일러",
        "NET": "클라우드플레어", "OKTA": "옥타", "FTNT": "포티넷",
        "PLTR": "팔란티어", "ARM": "ARM", "ASML": "ASML",
        "AMAT": "어플라이드머티어리얼즈", "LRCX": "램리서치",
        "KLAC": "KLA", "MRVL": "마벨", "ON": "온세미",
        "TXN": "텍사스인스트루먼트", "ADI": "아날로그디바이시스",
        "JPM": "JP모건", "BAC": "뱅크오브아메리카", "GS": "골드만삭스",
        "MS": "모건스탠리", "WFC": "웰스파고", "C": "씨티그룹",
        "BX": "블랙스톤", "KKR": "KKR", "BLK": "블랙록",
        "WMT": "월마트", "COST": "코스트코", "HD": "홈디포",
        "TGT": "타깃", "NKE": "나이키", "SBUX": "스타벅스",
        "MCD": "맥도날드", "PG": "P&G", "KO": "코카콜라", "PEP": "펩시코",
        "XOM": "엑슨모빌", "CVX": "쉐브론", "COP": "코노코필립스",
        "LLY": "일라이릴리", "JNJ": "존슨앤존슨", "PFE": "화이자",
        "MRK": "머크", "ABBV": "애브비", "UNH": "유나이티드헬스",
        "MRNA": "모더나", "BNTX": "바이오엔텍", "ISRG": "인튜이티브서지컬",
        "LMT": "록히드마틴", "RTX": "레이시온", "NOC": "노스럽그루먼",
        "GD": "제너럴다이나믹스", "BA": "보잉",
        "RIVN": "리비안", "LCID": "루시드", "NIO": "니오",
        "XPEV": "샤오펑", "LI": "리오토",
        "COIN": "코인베이스", "MSTR": "마이크로스트래티지",
        "SMCI": "슈퍼마이크로", "DELL": "델",
        "RKLB": "로켓랩", "JOBY": "조비에비에이션", "ACHR": "아처에비에이션",
        "PLUG": "플러그파워", "FSLR": "퍼스트솔라", "ENPH": "엔페이즈",
        "CRSP": "크리스퍼", "BEAM": "빔테라퓨틱스", "EDIT": "에디타스",
        "V": "비자", "MA": "마스터카드", "PYPL": "페이팔", "SQ": "블록",
        "UBER": "우버", "ABNB": "에어비앤비", "DASH": "도어대시",
        "SPOT": "스포티파이", "RBLX": "로블록스", "APP": "앱러빈",
        "SPY": "S&P500ETF", "QQQ": "나스닥ETF", "SOXX": "반도체ETF",
        "TQQQ": "나스닥3배레버리지", "SOXL": "반도체3배레버리지",
        "ARKK": "ARK이노베이션", "GLD": "금ETF", "TLT": "미국채ETF",
        "IBIT": "비트코인ETF",
    }

    base    = symbol.split(".")[0] if "." in symbol else symbol
    kr_name = OVERSEAS_KR.get(base, "")
    query   = kr_name if kr_name else base

    results = []

    # ── 네이버 공식 API 사용 ──────────────────────────────
    if client_id and client_secret:
        try:
            import urllib.parse
            enc_query = urllib.parse.quote(f"{query} 주식")
            api_url   = f"https://openapi.naver.com/v1/search/news.json?query={enc_query}&sort=date&display={limit}"
            headers   = {
                "X-Naver-Client-Id":     client_id,
                "X-Naver-Client-Secret": client_secret,
            }
            res  = requests.get(api_url, headers=headers, timeout=8)
            data = res.json()

            for item in data.get("items", []):
                title = re.sub(r"<[^>]+>", "", item.get("title", ""))
                link  = item.get("originallink") or item.get("link", "")
                date  = item.get("pubDate", "")
                # 날짜 변환
                try:
                    from datetime import datetime
                    dt  = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S +0900")
                    pub = dt.strftime("%Y.%m.%d %H:%M")
                except Exception:
                    pub = date[:10] if date else ""

                results.append({
                    "title":      title,
                    "url":        link,
                    "source":     item.get("description", "")[:20] if item.get("description") else "네이버뉴스",
                    "date":       pub,
                    "isOriginal": True,
                })
            return results
        except Exception as e:
            print(f"[뉴스] 네이버 API 오류: {e}")

    # ── 폴백: 네이버 검색 크롤링 ─────────────────────────
    try:
        import urllib.parse
        enc_query  = urllib.parse.quote(f"{query} 주식")
        search_url = f"https://search.naver.com/search.naver?where=news&query={enc_query}&sort=1"
        res        = requests.get(search_url, headers=_random_ua(), timeout=8)
        soup       = BeautifulSoup(res.text, "html.parser")

        items = (
            soup.select("div.news_wrap") or
            soup.select("ul.list_news li") or
            soup.select(".news_area") or
            []
        )[:limit]

        for item in items:
            title_tag = item.select_one("a.news_tit") or item.select_one("a")
            if not title_tag:
                continue
            results.append({
                "title":      title_tag.get_text(strip=True),
                "url":        title_tag.get("href", ""),
                "source":     "네이버뉴스",
                "date":       "",
                "isOriginal": False,
            })
    except Exception as e:
        print(f"[뉴스] 검색 폴백 오류: {e}")

    return results


def analyze_news_sentiment(news_list: list[dict]) -> dict:
    """뉴스 목록 전체 감성 집계"""
    if not news_list:
        return {
            "overall":          0.0,
            "label":            "neutral",
            "positiveKeywords": [],
            "negativeKeywords": [],
        }

    scores  = [n.get("sentimentScore", 0) for n in news_list]
    overall = round(sum(scores) / len(scores), 2)
    label   = (
        "positive" if overall >  0.1 else
        "negative" if overall < -0.1 else
        "neutral"
    )

    all_keywords = []
    for n in news_list:
        all_keywords.extend(n.get("keywords", []))

    pos_kw = list(dict.fromkeys(
        k for k in all_keywords if k in POSITIVE_WORDS
    ))[:10]
    neg_kw = list(dict.fromkeys(
        k for k in all_keywords if k in NEGATIVE_WORDS
    ))[:10]

    return {
        "overall":          overall,
        "label":            label,
        "positiveKeywords": pos_kw,
        "negativeKeywords": neg_kw,
    }
