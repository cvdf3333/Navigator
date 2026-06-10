"""
OpenDART API 연동 모듈
https://opendart.fss.or.kr/
"""
import os
import requests
from datetime import datetime, timedelta
from typing import Optional

DART_API_KEY = os.environ.get("DART_API_KEY", "8b57418f6cd16c247c69d6f025ee377cdad03c7d")
DART_BASE_URL = "https://opendart.fss.or.kr/api"


def get_corp_code(company_name: str) -> Optional[str]:
    """회사명으로 DART 고유번호 조회"""
    url = f"{DART_BASE_URL}/corpCode.xml"
    try:
        resp = requests.get(url, params={"crtfc_key": DART_API_KEY}, timeout=10)
        if resp.status_code != 200:
            return None
        import xml.etree.ElementTree as ET
        import zipfile
        import io
        with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
            with z.open("CORPCODE.xml") as f:
                tree = ET.parse(f)
                root = tree.getroot()
                for corp in root.findall("list"):
                    name = corp.findtext("corp_name", "")
                    code = corp.findtext("corp_code", "")
                    if company_name.lower() in name.lower():
                        return code
    except Exception:
        pass
    return None


def get_recent_disclosures(corp_code: str, limit: int = 5) -> list[dict]:
    """최근 공시 목록 조회"""
    url = f"{DART_BASE_URL}/list.json"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": corp_code,
        "bgn_de": start_date.strftime("%Y%m%d"),
        "end_de": end_date.strftime("%Y%m%d"),
        "page_count": limit,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get("status") == "000" and data.get("list"):
            return [
                {
                    "title": item.get("report_nm", ""),
                    "type": item.get("pblntf_ty", ""),
                    "submittedAt": item.get("rcept_dt", ""),
                    "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={item.get('rcept_no', '')}",
                    "grade": "A",
                    "corp_name": item.get("corp_name", ""),
                    "rcept_no": item.get("rcept_no", ""),
                }
                for item in data["list"][:limit]
            ]
    except Exception as e:
        pass
    return []


def get_financial_statements(corp_code: str, year: str = None, report_code: str = "11011") -> dict:
    """재무제표 조회 (단일회사 주요계정)"""
    if year is None:
        year = str(datetime.now().year - 1)

    url = f"{DART_BASE_URL}/fnlttSinglAcntAll.json"
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": corp_code,
        "bsns_year": year,
        "reprt_code": report_code,
        "fs_div": "CFS",
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get("status") == "000" and data.get("list"):
            return {
                "year": year,
                "items": data["list"],
                "grade": "A",
                "source": "DART 공시원문",
            }
    except Exception:
        pass
    return {}


CORP_CODE_CACHE: dict[str, str] = {
    # ── 반도체 ───────────────────────────────────────────
    "삼성전자":           "00126380",
    "SK하이닉스":         "00164779",
    "삼성전기":           "00126371",
    "DB하이텍":           "00104396",
    "리노공업":           "00347551",

    # ── IT/인터넷 ────────────────────────────────────────
    "NAVER":              "00266961",
    "네이버":             "00266961",
    "카카오":             "00918444",
    "삼성에스디에스":     "00126186",
    "LG CNS":             "00546782",
    "한글과컴퓨터":       "00179023",

    # ── 자동차 ───────────────────────────────────────────
    "현대차":             "00164742",
    "현대자동차":         "00164742",
    "기아":               "00106641",
    "현대모비스":         "00164560",

    # ── 화학/소재 ────────────────────────────────────────
    "LG화학":             "00109901",
    "삼성SDI":            "00126399",
    "SK이노베이션":       "00403927",
    "롯데케미칼":         "00119650",
    "금호석유":           "00101719",
    "효성첨단소재":       "00631518",

    # ── 바이오/헬스케어 ──────────────────────────────────
    "삼성바이오로직스":   "00877059",
    "셀트리온":           "00153153",
    "유한양행":           "00100840",
    "한미약품":           "00373580",
    "대웅제약":           "00099687",
    "종근당":             "00102043",
    "녹십자":             "00100469",
    "에코프로비엠":       "01407247",
    "에코프로":           "00231567",

    # ── 금융 ─────────────────────────────────────────────
    "KB금융":             "00798849",
    "신한지주":           "00382199",
    "하나금융지주":       "01041175",
    "우리금융지주":       "01003078",
    "삼성생명":           "00131536",
    "삼성화재":           "00131539",
    "미래에셋증권":       "00322885",
    "키움증권":           "00296290",
    "NH투자증권":         "00261492",
    "한국투자증권":       "00159643",
    "삼성증권":           "00126372",

    # ── 에너지/유틸리티 ──────────────────────────────────
    "한국전력":           "00008311",
    "SK텔레콤":           "00140575",
    "KT":                 "00156228",
    "SK":                 "00164740",
    "GS":                 "00478817",
    "S-Oil":              "00104782",

    # ── 철강/중공업 ──────────────────────────────────────
    "포스코홀딩스":       "00164473",
    "POSCO홀딩스":        "00164473",
    "현대제철":           "00164555",
    "고려아연":           "00096785",

    # ── 조선/방산 ────────────────────────────────────────
    "HD한국조선해양":     "00164963",
    "삼성중공업":         "00126188",
    "한화에어로스페이스": "00100536",
    "한국항공우주":       "00547583",
    "LIG넥스원":          "00382578",
    "현대로템":           "00164551",
    "한화오션":           "00164840",

    # ── 소비/유통 ────────────────────────────────────────
    "LG전자":             "00401345",
    "삼성물산":           "00126379",
    "롯데쇼핑":           "00117694",
    "이마트":             "00631152",
    "현대백화점":         "00105764",
    "신세계":             "00096742",
    "CJ제일제당":         "00080935",

    # ── 엔터/미디어/게임 ─────────────────────────────────
    "하이브":             "01041194",
    "SM엔터테인먼트":     "00520711",
    "JYP엔터테인먼트":    "00315849",
    "와이지엔터테인먼트": "00315845",
    "크래프톤":           "01366684",
    "넷마블":             "01165388",
    "엔씨소프트":         "00231748",
    "카카오게임즈":       "01399420",

    # ── 2차전지/에너지 ───────────────────────────────────
    "LG에너지솔루션":     "01483494",
    "포스코퓨처엠":       "00164466",
    "에코프로머티리얼즈": "01759766",
    "코스모신소재":       "00104714",

    # ── 건설/부동산 ──────────────────────────────────────
    "삼성물산건설":       "00126379",
    "현대건설":           "00164783",
    "GS건설":             "00404189",
    "대우건설":           "00104045",
    "DL이앤씨":           "00251019",

    # ── 항공/운송 ────────────────────────────────────────
    "대한항공":           "00112966",
    "아시아나항공":       "00403459",
    "제주항공":           "00779781",
    "HMM":                "00159096",
    "팬오션":             "00163268",
    "CJ대한통운":         "00095671",

    # ── 코스닥 주요 종목 ─────────────────────────────────
    "알테오젠":           "00700827",
    "셀트리온헬스케어":   "01064502",
    "펄어비스":           "01168884",
    "카카오뱅크":         "01440207",
    "카카오페이":         "01474218",
    "두산로보틱스":       "01799699",
    "레인보우로보틱스":   "01260643",
    "HD현대":             "00164947",
}

def get_corp_code_cached(company_name: str) -> Optional[str]:
    """
    회사명으로 DART 코드 조회
    1순위: 정확히 일치
    2순위: 부분 일치 (예: "현대차" → "현대자동차" 매칭)
    3순위: DART API 직접 조회
    """
    # 1순위: 정확히 일치
    if company_name in CORP_CODE_CACHE:
        return CORP_CODE_CACHE[company_name]

    # 2순위: 부분 일치 검색
    # "현대차"로 검색하면 "현대자동차" 키도 찾아줌
    for cached_name, code in CORP_CODE_CACHE.items():
        if company_name in cached_name or cached_name in company_name:
            return code

    # 3순위: DART API 직접 조회 (느림 — 캐시에 없을 때만)
    print(f"[DART] '{company_name}' 캐시 없음 → API 직접 조회")
    return get_corp_code(company_name)
