"""
yfinance 기반 주가 데이터 수집 모듈
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

PERIOD_MAP = {
    "1일": "1d",
    "5일": "5d",
    "1개월": "1mo",
    "3개월": "3mo",
    "6개월": "6mo",
    "1년": "1y",
    "2년": "2y",
    "5년": "5y",
}

POPULAR_STOCKS = [
    {
        "symbol": "005930.KS",
        "name": "삼성전자",
        "market": "KRX"
    },
    {
        "symbol": "000660.KS",
        "name": "SK하이닉스",
        "market": "KRX"
    },
    {
        "symbol": "035420.KS",
        "name": "NAVER",
        "market": "KRX"
    },
    {
        "symbol": "051910.KS",
        "name": "LG화학",
        "market": "KRX"
    },
    {
        "symbol": "006400.KS",
        "name": "삼성SDI",
        "market": "KRX"
    },
    {
        "symbol": "035720.KS",
        "name": "카카오",
        "market": "KRX"
    },
    {
        "symbol": "068270.KS",
        "name": "셀트리온",
        "market": "KRX"
    },
    {
        "symbol": "207940.KS",
        "name": "삼성바이오로직스",
        "market": "KRX"
    },
    {
        "symbol": "000270.KS",
        "name": "기아",
        "market": "KRX"
    },
    {
        "symbol": "005380.KS",
        "name": "현대차",
        "market": "KRX"
    },
    {
        "symbol": "012330.KS",
        "name": "현대모비스",
        "market": "KRX"
    },
    {
        "symbol": "096770.KS",
        "name": "SK이노베이션",
        "market": "KRX"
    },
    {
        "symbol": "034730.KS",
        "name": "SK",
        "market": "KRX"
    },
    {
        "symbol": "028260.KS",
        "name": "삼성물산",
        "market": "KRX"
    },
    {
        "symbol": "066570.KS",
        "name": "LG전자",
        "market": "KRX"
    },
    {
        "symbol": "003550.KS",
        "name": "LG",
        "market": "KRX"
    },
    {
        "symbol": "015760.KS",
        "name": "한국전력",
        "market": "KRX"
    },
    {
        "symbol": "017670.KS",
        "name": "SK텔레콤",
        "market": "KRX"
    },
    {
        "symbol": "030200.KS",
        "name": "KT",
        "market": "KRX"
    },
    {
        "symbol": "086790.KS",
        "name": "하나금융지주",
        "market": "KRX"
    },
    {
        "symbol": "105560.KS",
        "name": "KB금융",
        "market": "KRX"
    },
    {
        "symbol": "055550.KS",
        "name": "신한지주",
        "market": "KRX"
    },
    {
        "symbol": "316140.KS",
        "name": "우리금융지주",
        "market": "KRX"
    },
    {
        "symbol": "032830.KS",
        "name": "삼성생명",
        "market": "KRX"
    },
    {
        "symbol": "018260.KS",
        "name": "삼성에스디에스",
        "market": "KRX"
    },
    {
        "symbol": "009150.KS",
        "name": "삼성전기",
        "market": "KRX"
    },
    {
        "symbol": "011200.KS",
        "name": "HMM",
        "market": "KRX"
    },
    {
        "symbol": "047050.KS",
        "name": "포스코홀딩스",
        "market": "KRX"
    },
    {
        "symbol": "000100.KS",
        "name": "유한양행",
        "market": "KRX"
    },
    {
        "symbol": "010130.KS",
        "name": "고려아연",
        "market": "KRX"
    },
    {
        "symbol": "009830.KS",
        "name": "한화솔루션",
        "market": "KRX"
    },
    {
        "symbol": "010950.KS",
        "name": "S-Oil",
        "market": "KRX"
    },
    {
        "symbol": "078930.KS",
        "name": "GS",
        "market": "KRX"
    },
    {
        "symbol": "161890.KS",
        "name": "한국콜마",
        "market": "KRX"
    },
    {
        "symbol": "000720.KS",
        "name": "현대건설",
        "market": "KRX"
    },
    {
        "symbol": "005490.KS",
        "name": "POSCO홀딩스",
        "market": "KRX"
    },
    {
        "symbol": "373220.KS",
        "name": "LG에너지솔루션",
        "market": "KRX"
    },
    {
        "symbol": "003670.KS",
        "name": "포스코퓨처엠",
        "market": "KRX"
    },
    {
        "symbol": "041510.KS",
        "name": "에스엠",
        "market": "KRX"
    },
    {
        "symbol": "352820.KS",
        "name": "하이브",
        "market": "KRX"
    },
    {
        "symbol": "259960.KS",
        "name": "크래프톤",
        "market": "KRX"
    },
    {
        "symbol": "036570.KS",
        "name": "엔씨소프트",
        "market": "KRX"
    },
    {
        "symbol": "251270.KS",
        "name": "넷마블",
        "market": "KRX"
    },
    {
        "symbol": "139480.KS",
        "name": "이마트",
        "market": "KRX"
    },
    {
        "symbol": "097950.KS",
        "name": "CJ제일제당",
        "market": "KRX"
    },
    {
        "symbol": "271560.KS",
        "name": "오리온",
        "market": "KRX"
    },
    {
        "symbol": "008770.KS",
        "name": "호텔신라",
        "market": "KRX"
    },
    {
        "symbol": "000080.KS",
        "name": "하이트진로",
        "market": "KRX"
    },
    {
        "symbol": "021240.KS",
        "name": "코웨이",
        "market": "KRX"
    },
    {
        "symbol": "000810.KS",
        "name": "삼성화재",
        "market": "KRX"
    },
    {
        "symbol": "005830.KS",
        "name": "DB손해보험",
        "market": "KRX"
    },
    {
        "symbol": "005940.KS",
        "name": "NH투자증권",
        "market": "KRX"
    },
    {
        "symbol": "016360.KS",
        "name": "삼성증권",
        "market": "KRX"
    },
    {
        "symbol": "006800.KS",
        "name": "미래에셋증권",
        "market": "KRX"
    },
    {
        "symbol": "071050.KS",
        "name": "한국금융지주",
        "market": "KRX"
    },
    {
        "symbol": "010140.KS",
        "name": "삼성중공업",
        "market": "KRX"
    },
    {
        "symbol": "009540.KS",
        "name": "HD한국조선해양",
        "market": "KRX"
    },
    {
        "symbol": "042660.KS",
        "name": "한화오션",
        "market": "KRX"
    },
    {
        "symbol": "329180.KS",
        "name": "HD현대중공업",
        "market": "KRX"
    },
    {
        "symbol": "267250.KS",
        "name": "HD현대",
        "market": "KRX"
    },
    {
        "symbol": "010620.KS",
        "name": "현대미포조선",
        "market": "KRX"
    },
    {
        "symbol": "064350.KS",
        "name": "현대로템",
        "market": "KRX"
    },
    {
        "symbol": "034020.KS",
        "name": "두산에너빌리티",
        "market": "KRX",
        "sector": "방산/원전"
    },
    {
        "symbol": "012450.KS",
        "name": "한화에어로스페이스",
        "market": "KRX"
    },
    {
        "symbol": "047810.KS",
        "name": "한국항공우주(KAI)",
        "market": "KRX"
    },
    {
        "symbol": "272210.KS",
        "name": "한화시스템",
        "market": "KRX"
    },
    {
        "symbol": "003490.KS",
        "name": "대한항공",
        "market": "KRX"
    },
    {
        "symbol": "020560.KS",
        "name": "아시아나항공",
        "market": "KRX"
    },
    {
        "symbol": "028670.KS",
        "name": "팬오션",
        "market": "KRX"
    },
    {
        "symbol": "000120.KS",
        "name": "CJ대한통운",
        "market": "KRX"
    },
    {
        "symbol": "011170.KS",
        "name": "롯데케미칼",
        "market": "KRX"
    },
    {
        "symbol": "004000.KS",
        "name": "롯데정밀화학",
        "market": "KRX"
    },
    {
        "symbol": "010060.KS",
        "name": "OCI홀딩스",
        "market": "KRX"
    },
    {
        "symbol": "002380.KS",
        "name": "KCC",
        "market": "KRX"
    },
    {
        "symbol": "071840.KS",
        "name": "롯데하이마트",
        "market": "KRX"
    },
    {
        "symbol": "023530.KS",
        "name": "롯데쇼핑",
        "market": "KRX"
    },
    {
        "symbol": "007070.KS",
        "name": "GS리테일",
        "market": "KRX"
    },
    {
        "symbol": "069960.KS",
        "name": "현대백화점",
        "market": "KRX"
    },
    {
        "symbol": "004170.KS",
        "name": "신세계",
        "market": "KRX"
    },
    {
        "symbol": "000880.KS",
        "name": "한화",
        "market": "KRX"
    },
    {
        "symbol": "001040.KS",
        "name": "CJ",
        "market": "KRX"
    },
    {
        "symbol": "000210.KS",
        "name": "DL",
        "market": "KRX"
    },
    {
        "symbol": "180640.KS",
        "name": "한진칼",
        "market": "KRX"
    },
    {
        "symbol": "005180.KS",
        "name": "빙그레",
        "market": "KRX"
    },
    {
        "symbol": "007310.KS",
        "name": "오뚜기",
        "market": "KRX"
    },
    {
        "symbol": "277810.KQ",
        "name": "레인보우로보틱스",
        "market": "KOSDAQ"
    },
    {
        "symbol": "326030.KQ",
        "name": "SK바이오팜",
        "market": "KOSDAQ"
    },
    {
        "symbol": "263750.KQ",
        "name": "펄어비스",
        "market": "KOSDAQ"
    },
    {
        "symbol": "357780.KQ",
        "name": "솔브레인",
        "market": "KOSDAQ"
    },
    {
        "symbol": "247540.KQ",
        "name": "에코프로비엠",
        "market": "KOSDAQ"
    },
    {
        "symbol": "086520.KQ",
        "name": "에코프로",
        "market": "KOSDAQ"
    },
    {
        "symbol": "196170.KQ",
        "name": "알테오젠",
        "market": "KOSDAQ"
    },
    {
        "symbol": "214150.KQ",
        "name": "클래시스",
        "market": "KOSDAQ"
    },
    {
        "symbol": "112040.KQ",
        "name": "위메이드",
        "market": "KOSDAQ"
    },
    {
        "symbol": "058470.KQ",
        "name": "리노공업",
        "market": "KOSDAQ"
    },
    {
        "symbol": "145720.KQ",
        "name": "덴티움",
        "market": "KOSDAQ"
    },
    {
        "symbol": "035900.KQ",
        "name": "JYP엔터테인먼트",
        "market": "KOSDAQ"
    },
    {
        "symbol": "122870.KQ",
        "name": "와이지엔터테인먼트",
        "market": "KOSDAQ"
    },
    {
        "symbol": "091990.KQ",
        "name": "셀트리온헬스케어",
        "market": "KOSDAQ"
    },
    {
        "symbol": "068760.KQ",
        "name": "셀트리온제약",
        "market": "KOSDAQ"
    },
    {
        "symbol": "039030.KQ",
        "name": "이오테크닉스",
        "market": "KOSDAQ"
    },
    {
        "symbol": "095610.KQ",
        "name": "테스",
        "market": "KOSDAQ"
    },
    {
        "symbol": "403870.KQ",
        "name": "HPSP",
        "market": "KOSDAQ"
    },
    {
        "symbol": "036540.KQ",
        "name": "SFA반도체",
        "market": "KOSDAQ"
    },
    {
        "symbol": "067310.KQ",
        "name": "하나마이크론",
        "market": "KOSDAQ"
    },
    {
        "symbol": "089030.KQ",
        "name": "테크윙",
        "market": "KOSDAQ"
    },
    {
        "symbol": "064760.KQ",
        "name": "티씨케이",
        "market": "KOSDAQ"
    },
    {
        "symbol": "298380.KQ",
        "name": "에이비엘바이오",
        "market": "KOSDAQ"
    },
    {
        "symbol": "060280.KQ",
        "name": "큐렉소",
        "market": "KOSDAQ"
    },
    {
        "symbol": "140860.KQ",
        "name": "파크시스템스",
        "market": "KOSDAQ"
    },
    {
        "symbol": "335890.KQ",
        "name": "비올",
        "market": "KOSDAQ"
    },
    {
        "symbol": "285490.KQ",
        "name": "노을",
        "market": "KOSDAQ"
    },
    {
        "symbol": "215000.KQ",
        "name": "골프존",
        "market": "KOSDAQ"
    },
    {
        "symbol": "030520.KQ",
        "name": "한글과컴퓨터",
        "market": "KOSDAQ"
    },
    {
        "symbol": "241560.KQ",
        "name": "두산밥캣",
        "market": "KOSDAQ"
    },
    {
        "symbol": "370090.KQ",
        "name": "퓨런티어",
        "market": "KOSDAQ"
    },
    {
        "symbol": "090460.KQ",
        "name": "비에이치",
        "market": "KOSDAQ"
    },
    {
        "symbol": "007390.KQ",
        "name": "네오위즈",
        "market": "KOSDAQ"
    },
    {
        "symbol": "AAPL",
        "name": "애플 (Apple)",
        "market": "NASDAQ"
    },
    {
        "symbol": "MSFT",
        "name": "마이크로소프트 (Microsoft)",
        "market": "NASDAQ"
    },
    {
        "symbol": "NVDA",
        "name": "엔비디아 (NVIDIA)",
        "market": "NASDAQ"
    },
    {
        "symbol": "GOOGL",
        "name": "구글 알파벳 (Alphabet)",
        "market": "NASDAQ"
    },
    {
        "symbol": "AMZN",
        "name": "아마존 (Amazon)",
        "market": "NASDAQ"
    },
    {
        "symbol": "META",
        "name": "메타 (Meta Platforms)",
        "market": "NASDAQ"
    },
    {
        "symbol": "TSLA",
        "name": "테슬라 (Tesla)",
        "market": "NASDAQ"
    },
    {
        "symbol": "AVGO",
        "name": "브로드컴 (Broadcom)",
        "market": "NASDAQ"
    },
    {
        "symbol": "AMD",
        "name": "AMD",
        "market": "NASDAQ"
    },
    {
        "symbol": "INTC",
        "name": "인텔 (Intel)",
        "market": "NASDAQ"
    },
    {
        "symbol": "QCOM",
        "name": "퀄컴 (Qualcomm)",
        "market": "NASDAQ"
    },
    {
        "symbol": "MU",
        "name": "마이크론 (Micron)",
        "market": "NASDAQ"
    },
    {
        "symbol": "ASML",
        "name": "ASML (노광장비)",
        "market": "NASDAQ"
    },
    {
        "symbol": "ARM",
        "name": "ARM 홀딩스",
        "market": "NASDAQ"
    },
    {
        "symbol": "NFLX",
        "name": "넷플릭스 (Netflix)",
        "market": "NASDAQ"
    },
    {
        "symbol": "CRM",
        "name": "세일즈포스 (Salesforce)",
        "market": "NYSE"
    },
    {
        "symbol": "ORCL",
        "name": "오라클 (Oracle)",
        "market": "NYSE"
    },
    {
        "symbol": "ADBE",
        "name": "어도비 (Adobe)",
        "market": "NASDAQ"
    },
    {
        "symbol": "NOW",
        "name": "서비스나우 (ServiceNow)",
        "market": "NYSE"
    },
    {
        "symbol": "PLTR",
        "name": "팔란티어 (Palantir)",
        "market": "NASDAQ"
    },
    {
        "symbol": "JPM",
        "name": "JP모건체이스 (JPMorgan)",
        "market": "NYSE"
    },
    {
        "symbol": "BAC",
        "name": "뱅크오브아메리카 (BofA)",
        "market": "NYSE"
    },
    {
        "symbol": "GS",
        "name": "골드만삭스 (Goldman Sachs)",
        "market": "NYSE"
    },
    {
        "symbol": "MS",
        "name": "모건스탠리 (Morgan Stanley)",
        "market": "NYSE"
    },
    {
        "symbol": "WMT",
        "name": "월마트 (Walmart)",
        "market": "NYSE"
    },
    {
        "symbol": "COST",
        "name": "코스트코 (Costco)",
        "market": "NASDAQ"
    },
    {
        "symbol": "HD",
        "name": "홈디포 (Home Depot)",
        "market": "NYSE"
    },
    {
        "symbol": "MCD",
        "name": "맥도날드 (McDonald's)",
        "market": "NYSE"
    },
    {
        "symbol": "SBUX",
        "name": "스타벅스 (Starbucks)",
        "market": "NASDAQ"
    },
    {
        "symbol": "JNJ",
        "name": "존슨앤존슨 (J&J)",
        "market": "NYSE"
    },
    {
        "symbol": "PFE",
        "name": "화이자 (Pfizer)",
        "market": "NYSE"
    },
    {
        "symbol": "LLY",
        "name": "일라이릴리 (Eli Lilly)",
        "market": "NYSE"
    },
    {
        "symbol": "UNH",
        "name": "유나이티드헬스 (UnitedHealth)",
        "market": "NYSE"
    },
    {
        "symbol": "XOM",
        "name": "엑슨모빌 (ExxonMobil)",
        "market": "NYSE"
    },
    {
        "symbol": "CVX",
        "name": "셰브론 (Chevron)",
        "market": "NYSE"
    },
    {
        "symbol": "SPY",
        "name": "SPDR S&P500 ETF",
        "market": "NYSE"
    },
    {
        "symbol": "QQQ",
        "name": "나스닥100 ETF (QQQ)",
        "market": "NASDAQ"
    },
    {
        "symbol": "SOXX",
        "name": "필라델피아 반도체 ETF (SOXX)",
        "market": "NASDAQ"
    },
    {
        "symbol": "ARKK",
        "name": "ARK 이노베이션 ETF",
        "market": "NYSE"
    },
    {
        "symbol": "079550.KS",
        "name": "LIG넥스원",
        "market": "KRX",
        "sector": "방산"
    },
    {
        "symbol": "336370.KQ",
        "name": "솔브레인홀딩스",
        "market": "KOSDAQ",
        "sector": "반도체소재"
    },
    {
        "symbol": "036930.KQ",
        "name": "주성엔지니어링",
        "market": "KOSDAQ",
        "sector": "반도체장비"
    },
    {
        "symbol": "041510.KQ",
        "name": "에스엠",
        "market": "KOSDAQ",
        "sector": "엔터"
    },
    {
        "symbol": "352820.KQ",
        "name": "하이브",
        "market": "KOSDAQ",
        "sector": "엔터"
    },
    {
        "symbol": "108860.KQ",
        "name": "셀바스AI",
        "market": "KOSDAQ",
        "sector": "로봇/AI"
    },
    {
        "symbol": "950130.KQ",
        "name": "엑스게이트",
        "market": "KOSDAQ",
        "sector": "로봇/AI"
    },
    {
        "symbol": "SNOW",
        "name": "스노우플레이크",
        "market": "NASDAQ",
        "sector": "클라우드"
    },
    {
        "symbol": "UBER",
        "name": "우버",
        "market": "NASDAQ",
        "sector": "플랫폼"
    },
    {
        "symbol": "ABNB",
        "name": "에어비앤비",
        "market": "NASDAQ",
        "sector": "플랫폼"
    },
    {
        "symbol": "COIN",
        "name": "코인베이스",
        "market": "NASDAQ",
        "sector": "가상자산"
    },
    {
        "symbol": "MSTR",
        "name": "마이크로스트래티지",
        "market": "NASDAQ",
        "sector": "가상자산"
    },
    {
        "symbol": "SMCI",
        "name": "슈퍼마이크로컴퓨터",
        "market": "NASDAQ",
        "sector": "AI인프라"
    },
    {
        "symbol": "DELL",
        "name": "델 테크놀로지스",
        "market": "NASDAQ",
        "sector": "AI인프라"
    },
    {
        "symbol": "BRK-B",
        "name": "버크셔해서웨이",
        "market": "NYSE",
        "sector": "금융"
    },
    {
        "symbol": "000990.KS",
        "name": "DB하이텍",
        "market": "KRX",
        "sector": "반도체"
    },
    {
        "symbol": "102110.KQ",
        "name": "ISC",
        "market": "KOSDAQ",
        "sector": "반도체"
    },
    {
        "symbol": "033240.KQ",
        "name": "자화전자",
        "market": "KOSDAQ",
        "sector": "전자부품"
    },
    {
        "symbol": "009450.KS",
        "name": "경동나비엔",
        "market": "KRX",
        "sector": "가전"
    },
    {
        "symbol": "011210.KS",
        "name": "현대위아",
        "market": "KRX",
        "sector": "자동차부품"
    },
    {
        "symbol": "018880.KS",
        "name": "한온시스템",
        "market": "KRX",
        "sector": "자동차부품"
    },
    {
        "symbol": "004020.KS",
        "name": "현대제철",
        "market": "KRX",
        "sector": "철강"
    },
    {
        "symbol": "103140.KQ",
        "name": "풍산",
        "market": "KOSDAQ",
        "sector": "비철금속"
    },
    {
        "symbol": "002790.KS",
        "name": "아모레G",
        "market": "KRX",
        "sector": "화장품"
    },
    {
        "symbol": "090430.KS",
        "name": "아모레퍼시픽",
        "market": "KRX",
        "sector": "화장품"
    },
    {
        "symbol": "051600.KS",
        "name": "한전KPS",
        "market": "KRX",
        "sector": "전력"
    },
    {
        "symbol": "036460.KS",
        "name": "한국가스공사",
        "market": "KRX",
        "sector": "가스"
    },
    {
        "symbol": "047040.KS",
        "name": "대우건설",
        "market": "KRX",
        "sector": "건설"
    },
    {
        "symbol": "028050.KS",
        "name": "삼성엔지니어링",
        "market": "KRX",
        "sector": "건설"
    },
    {
        "symbol": "006360.KS",
        "name": "GS건설",
        "market": "KRX",
        "sector": "건설"
    },
    {
        "symbol": "282330.KS",
        "name": "BGF리테일",
        "market": "KRX",
        "sector": "유통"
    },
    {
        "symbol": "003230.KS",
        "name": "삼양식품",
        "market": "KRX",
        "sector": "식품"
    },
    {
        "symbol": "032640.KS",
        "name": "LG유플러스",
        "market": "KRX",
        "sector": "통신"
    },
    {
        "symbol": "053210.KQ",
        "name": "스튜디오드래곤",
        "market": "KOSDAQ",
        "sector": "미디어"
    },
    {
        "symbol": "067160.KQ",
        "name": "아프리카TV",
        "market": "KOSDAQ",
        "sector": "미디어"
    },
    {
        "symbol": "088350.KS",
        "name": "한화생명",
        "market": "KRX",
        "sector": "보험"
    },
    {
        "symbol": "039490.KS",
        "name": "키움증권",
        "market": "KRX",
        "sector": "증권"
    },
    {
        "symbol": "069620.KQ",
        "name": "대웅제약",
        "market": "KOSDAQ",
        "sector": "제약"
    },
    {
        "symbol": "128940.KS",
        "name": "한미약품",
        "market": "KRX",
        "sector": "제약"
    },
    {
        "symbol": "051900.KS",
        "name": "LG생활건강",
        "market": "KRX",
        "sector": "화장품"
    },
    {
        "symbol": "011790.KS",
        "name": "SKC",
        "market": "KRX",
        "sector": "화학"
    },
    {
        "symbol": "091440.KQ",
        "name": "조이시티",
        "market": "KOSDAQ",
        "sector": "게임"
    },
    {
        "symbol": "054620.KQ",
        "name": "APS홀딩스",
        "market": "KOSDAQ",
        "sector": "반도체"
    },
    {
        "symbol": "101160.KQ",
        "name": "월덱스",
        "market": "KOSDAQ",
        "sector": "반도체소재"
    },
    {
        "symbol": "036830.KQ",
        "name": "솔브레인홀딩스",
        "market": "KOSDAQ",
        "sector": "반도체소재"
    },
    {
        "symbol": "GOOG",
        "name": "알파벳 C주 (GOOG)",
        "market": "NASDAQ",
        "sector": "기술"
    },
    {
        "symbol": "AMAT",
        "name": "어플라이드머티어리얼즈",
        "market": "NASDAQ",
        "sector": "반도체장비"
    },
    {
        "symbol": "LRCX",
        "name": "램리서치",
        "market": "NASDAQ",
        "sector": "반도체장비"
    },
    {
        "symbol": "KLAC",
        "name": "KLA코퍼레이션",
        "market": "NASDAQ",
        "sector": "반도체장비"
    },
    {
        "symbol": "MRVL",
        "name": "마벨테크놀로지",
        "market": "NASDAQ",
        "sector": "반도체"
    },
    {
        "symbol": "ON",
        "name": "온세미컨덕터",
        "market": "NASDAQ",
        "sector": "반도체"
    },
    {
        "symbol": "TXN",
        "name": "텍사스인스트루먼트",
        "market": "NASDAQ",
        "sector": "반도체"
    },
    {
        "symbol": "ADI",
        "name": "아날로그디바이시스",
        "market": "NASDAQ",
        "sector": "반도체"
    },
    {
        "symbol": "DDOG",
        "name": "데이터도그",
        "market": "NASDAQ",
        "sector": "클라우드"
    },
    {
        "symbol": "ZS",
        "name": "지스케일러",
        "market": "NASDAQ",
        "sector": "사이버보안"
    },
    {
        "symbol": "CRWD",
        "name": "크라우드스트라이크",
        "market": "NASDAQ",
        "sector": "사이버보안"
    },
    {
        "symbol": "PANW",
        "name": "팔로알토네트웍스",
        "market": "NASDAQ",
        "sector": "사이버보안"
    },
    {
        "symbol": "OKTA",
        "name": "옥타",
        "market": "NASDAQ",
        "sector": "사이버보안"
    },
    {
        "symbol": "NET",
        "name": "클라우드플레어",
        "market": "NASDAQ",
        "sector": "클라우드"
    },
    {
        "symbol": "FTNT",
        "name": "포티넷",
        "market": "NASDAQ",
        "sector": "사이버보안"
    },
    {
        "symbol": "WDAY",
        "name": "워크데이",
        "market": "NASDAQ",
        "sector": "소프트웨어"
    },
    {
        "symbol": "INTU",
        "name": "인튜이트",
        "market": "NASDAQ",
        "sector": "소프트웨어"
    },
    {
        "symbol": "TEAM",
        "name": "아틀라시안",
        "market": "NASDAQ",
        "sector": "소프트웨어"
    },
    {
        "symbol": "ZM",
        "name": "줌비디오",
        "market": "NASDAQ",
        "sector": "소프트웨어"
    },
    {
        "symbol": "DOCU",
        "name": "도큐사인",
        "market": "NASDAQ",
        "sector": "소프트웨어"
    },
    {
        "symbol": "AI",
        "name": "C3.ai",
        "market": "NASDAQ",
        "sector": "AI"
    },
    {
        "symbol": "SOUN",
        "name": "사운드하운드AI",
        "market": "NASDAQ",
        "sector": "AI"
    },
    {
        "symbol": "BBAI",
        "name": "BigBear.ai",
        "market": "NASDAQ",
        "sector": "AI"
    },
    {
        "symbol": "HPE",
        "name": "HPE",
        "market": "NASDAQ",
        "sector": "AI인프라"
    },
    {
        "symbol": "RIVN",
        "name": "리비안",
        "market": "NASDAQ",
        "sector": "전기차"
    },
    {
        "symbol": "LCID",
        "name": "루시드모터스",
        "market": "NASDAQ",
        "sector": "전기차"
    },
    {
        "symbol": "NIO",
        "name": "니오",
        "market": "NASDAQ",
        "sector": "전기차"
    },
    {
        "symbol": "XPEV",
        "name": "샤오펑",
        "market": "NASDAQ",
        "sector": "전기차"
    },
    {
        "symbol": "LI",
        "name": "리오토",
        "market": "NASDAQ",
        "sector": "전기차"
    },
    {
        "symbol": "BYDDY",
        "name": "BYD",
        "market": "NASDAQ",
        "sector": "전기차"
    },
    {
        "symbol": "MRNA",
        "name": "모더나",
        "market": "NASDAQ",
        "sector": "바이오"
    },
    {
        "symbol": "BNTX",
        "name": "바이오엔텍",
        "market": "NASDAQ",
        "sector": "바이오"
    },
    {
        "symbol": "REGN",
        "name": "리제네론",
        "market": "NASDAQ",
        "sector": "바이오"
    },
    {
        "symbol": "VRTX",
        "name": "버텍스파마슈티컬스",
        "market": "NASDAQ",
        "sector": "바이오"
    },
    {
        "symbol": "ILMN",
        "name": "일루미나",
        "market": "NASDAQ",
        "sector": "바이오"
    },
    {
        "symbol": "ISRG",
        "name": "인튜이티브서지컬",
        "market": "NASDAQ",
        "sector": "의료로봇"
    },
    {
        "symbol": "HOOD",
        "name": "로빈후드",
        "market": "NASDAQ",
        "sector": "핀테크"
    },
    {
        "symbol": "SQ",
        "name": "블록(스퀘어)",
        "market": "NASDAQ",
        "sector": "핀테크"
    },
    {
        "symbol": "PYPL",
        "name": "페이팔",
        "market": "NASDAQ",
        "sector": "핀테크"
    },
    {
        "symbol": "LYFT",
        "name": "리프트",
        "market": "NASDAQ",
        "sector": "플랫폼"
    },
    {
        "symbol": "DASH",
        "name": "도어대시",
        "market": "NASDAQ",
        "sector": "플랫폼"
    },
    {
        "symbol": "SPOT",
        "name": "스포티파이",
        "market": "NASDAQ",
        "sector": "미디어"
    },
    {
        "symbol": "RBLX",
        "name": "로블록스",
        "market": "NASDAQ",
        "sector": "게임"
    },
    {
        "symbol": "U",
        "name": "유니티",
        "market": "NASDAQ",
        "sector": "게임엔진"
    },
    {
        "symbol": "EA",
        "name": "EA게임즈",
        "market": "NASDAQ",
        "sector": "게임"
    },
    {
        "symbol": "TTWO",
        "name": "테이크투인터랙티브",
        "market": "NASDAQ",
        "sector": "게임"
    },
    {
        "symbol": "WFC",
        "name": "웰스파고",
        "market": "NYSE",
        "sector": "금융"
    },
    {
        "symbol": "C",
        "name": "씨티그룹",
        "market": "NYSE",
        "sector": "금융"
    },
    {
        "symbol": "AXP",
        "name": "아메리칸익스프레스",
        "market": "NYSE",
        "sector": "금융"
    },
    {
        "symbol": "BX",
        "name": "블랙스톤",
        "market": "NYSE",
        "sector": "사모펀드"
    },
    {
        "symbol": "KKR",
        "name": "KKR",
        "market": "NYSE",
        "sector": "사모펀드"
    },
    {
        "symbol": "BLK",
        "name": "블랙록",
        "market": "NYSE",
        "sector": "자산운용"
    },
    {
        "symbol": "COP",
        "name": "코노코필립스",
        "market": "NYSE",
        "sector": "에너지"
    },
    {
        "symbol": "SLB",
        "name": "슐럼버거",
        "market": "NYSE",
        "sector": "에너지서비스"
    },
    {
        "symbol": "NEE",
        "name": "넥스테라에너지",
        "market": "NYSE",
        "sector": "신재생에너지"
    },
    {
        "symbol": "FSLR",
        "name": "퍼스트솔라",
        "market": "NASDAQ",
        "sector": "태양광"
    },
    {
        "symbol": "ENPH",
        "name": "엔페이즈에너지",
        "market": "NASDAQ",
        "sector": "태양광"
    },
    {
        "symbol": "RUN",
        "name": "선런",
        "market": "NASDAQ",
        "sector": "태양광"
    },
    {
        "symbol": "MRK",
        "name": "머크",
        "market": "NYSE",
        "sector": "제약"
    },
    {
        "symbol": "BMY",
        "name": "브리스톨마이어스",
        "market": "NYSE",
        "sector": "제약"
    },
    {
        "symbol": "ABBV",
        "name": "애브비",
        "market": "NYSE",
        "sector": "제약"
    },
    {
        "symbol": "CVS",
        "name": "CVS헬스",
        "market": "NYSE",
        "sector": "헬스케어"
    },
    {
        "symbol": "MDT",
        "name": "메드트로닉",
        "market": "NYSE",
        "sector": "의료기기"
    },
    {
        "symbol": "ABT",
        "name": "애보트래버러토리스",
        "market": "NYSE",
        "sector": "의료기기"
    },
    {
        "symbol": "LOW",
        "name": "로우스",
        "market": "NYSE",
        "sector": "소비재"
    },
    {
        "symbol": "TGT",
        "name": "타깃",
        "market": "NYSE",
        "sector": "소비재"
    },
    {
        "symbol": "NKE",
        "name": "나이키",
        "market": "NYSE",
        "sector": "스포츠"
    },
    {
        "symbol": "PG",
        "name": "P&G",
        "market": "NYSE",
        "sector": "생활용품"
    },
    {
        "symbol": "KO",
        "name": "코카콜라",
        "market": "NYSE",
        "sector": "식음료"
    },
    {
        "symbol": "PEP",
        "name": "펩시코",
        "market": "NASDAQ",
        "sector": "식음료"
    },
    {
        "symbol": "LMT",
        "name": "록히드마틴",
        "market": "NYSE",
        "sector": "방산"
    },
    {
        "symbol": "RTX",
        "name": "레이시온",
        "market": "NYSE",
        "sector": "방산"
    },
    {
        "symbol": "NOC",
        "name": "노스럽그루먼",
        "market": "NYSE",
        "sector": "방산"
    },
    {
        "symbol": "GD",
        "name": "제너럴다이나믹스",
        "market": "NYSE",
        "sector": "방산"
    },
    {
        "symbol": "BA",
        "name": "보잉",
        "market": "NYSE",
        "sector": "항공/방산"
    },
    {
        "symbol": "DAL",
        "name": "델타항공",
        "market": "NYSE",
        "sector": "항공"
    },
    {
        "symbol": "UAL",
        "name": "유나이티드항공",
        "market": "NASDAQ",
        "sector": "항공"
    },
    {
        "symbol": "T",
        "name": "AT&T",
        "market": "NYSE",
        "sector": "통신"
    },
    {
        "symbol": "VZ",
        "name": "버라이즌",
        "market": "NYSE",
        "sector": "통신"
    },
    {
        "symbol": "TMUS",
        "name": "T-모바일",
        "market": "NASDAQ",
        "sector": "통신"
    },
    {
        "symbol": "DIS",
        "name": "디즈니",
        "market": "NYSE",
        "sector": "미디어"
    },
    {
        "symbol": "CMCSA",
        "name": "컴캐스트",
        "market": "NASDAQ",
        "sector": "미디어"
    },
    {
        "symbol": "PARA",
        "name": "파라마운트글로벌",
        "market": "NASDAQ",
        "sector": "미디어"
    },
    {
        "symbol": "WBD",
        "name": "워너브라더스디스커버리",
        "market": "NASDAQ",
        "sector": "미디어"
    },
    {
        "symbol": "AMT",
        "name": "아메리칸타워",
        "market": "NYSE",
        "sector": "리츠"
    },
    {
        "symbol": "PLD",
        "name": "프롤로지스",
        "market": "NYSE",
        "sector": "리츠"
    },
    {
        "symbol": "EQIX",
        "name": "에퀴닉스",
        "market": "NASDAQ",
        "sector": "데이터센터리츠"
    },
    {
        "symbol": "DLR",
        "name": "디지털리얼티",
        "market": "NYSE",
        "sector": "데이터센터리츠"
    },
    {
        "symbol": "V",
        "name": "비자",
        "market": "NYSE",
        "sector": "결제"
    },
    {
        "symbol": "MA",
        "name": "마스터카드",
        "market": "NYSE",
        "sector": "결제"
    },
    {
        "symbol": "IVV",
        "name": "S&P500 ETF (IVV)",
        "market": "NYSE",
        "sector": "ETF"
    },
    {
        "symbol": "VOO",
        "name": "S&P500 ETF (VOO)",
        "market": "NYSE",
        "sector": "ETF"
    },
    {
        "symbol": "TQQQ",
        "name": "나스닥100 3배 레버리지",
        "market": "NASDAQ",
        "sector": "레버리지ETF"
    },
    {
        "symbol": "SQQQ",
        "name": "나스닥100 인버스 3배",
        "market": "NASDAQ",
        "sector": "인버스ETF"
    },
    {
        "symbol": "QLD",
        "name": "나스닥100 2배 레버리지",
        "market": "NASDAQ",
        "sector": "레버리지ETF"
    },
    {
        "symbol": "SSO",
        "name": "S&P500 2배 레버리지",
        "market": "NYSE",
        "sector": "레버리지ETF"
    },
    {
        "symbol": "UPRO",
        "name": "S&P500 3배 레버리지",
        "market": "NYSE",
        "sector": "레버리지ETF"
    },
    {
        "symbol": "SPXS",
        "name": "S&P500 인버스 3배",
        "market": "NYSE",
        "sector": "인버스ETF"
    },
    {
        "symbol": "DIA",
        "name": "다우존스 ETF (DIA)",
        "market": "NYSE",
        "sector": "ETF"
    },
    {
        "symbol": "IWM",
        "name": "러셀2000 ETF (IWM)",
        "market": "NYSE",
        "sector": "ETF"
    },
    {
        "symbol": "SMH",
        "name": "반도체 ETF (SMH)",
        "market": "NASDAQ",
        "sector": "섹터ETF"
    },
    {
        "symbol": "SOXL",
        "name": "반도체 3배 레버리지",
        "market": "NASDAQ",
        "sector": "레버리지ETF"
    },
    {
        "symbol": "SOXS",
        "name": "반도체 인버스 3배",
        "market": "NASDAQ",
        "sector": "인버스ETF"
    },
    {
        "symbol": "XLK",
        "name": "기술주 ETF (XLK)",
        "market": "NYSE",
        "sector": "섹터ETF"
    },
    {
        "symbol": "XLF",
        "name": "금융주 ETF (XLF)",
        "market": "NYSE",
        "sector": "섹터ETF"
    },
    {
        "symbol": "XLE",
        "name": "에너지 ETF (XLE)",
        "market": "NYSE",
        "sector": "섹터ETF"
    },
    {
        "symbol": "XLV",
        "name": "헬스케어 ETF (XLV)",
        "market": "NYSE",
        "sector": "섹터ETF"
    },
    {
        "symbol": "XLI",
        "name": "산업재 ETF (XLI)",
        "market": "NYSE",
        "sector": "섹터ETF"
    },
    {
        "symbol": "ARKG",
        "name": "ARK 유전체혁명 ETF",
        "market": "NYSE",
        "sector": "ETF"
    },
    {
        "symbol": "ARKW",
        "name": "ARK 차세대인터넷 ETF",
        "market": "NASDAQ",
        "sector": "ETF"
    },
    {
        "symbol": "BOTZ",
        "name": "로봇/AI ETF (BOTZ)",
        "market": "NASDAQ",
        "sector": "섹터ETF"
    },
    {
        "symbol": "ROBO",
        "name": "로봇공학 ETF (ROBO)",
        "market": "NASDAQ",
        "sector": "섹터ETF"
    },
    {
        "symbol": "ICLN",
        "name": "청정에너지 ETF",
        "market": "NASDAQ",
        "sector": "섹터ETF"
    },
    {
        "symbol": "TAN",
        "name": "태양광 ETF (TAN)",
        "market": "NYSE",
        "sector": "섹터ETF"
    },
    {
        "symbol": "LIT",
        "name": "리튬/배터리 ETF",
        "market": "NYSE",
        "sector": "섹터ETF"
    },
    {
        "symbol": "JETS",
        "name": "항공 ETF (JETS)",
        "market": "NYSE",
        "sector": "섹터ETF"
    },
    {
        "symbol": "ITA",
        "name": "방산 ETF (ITA)",
        "market": "NYSE",
        "sector": "섹터ETF"
    },
    {
        "symbol": "XBI",
        "name": "바이오테크 ETF (XBI)",
        "market": "NYSE",
        "sector": "섹터ETF"
    },
    {
        "symbol": "IBB",
        "name": "바이오테크 ETF (IBB)",
        "market": "NASDAQ",
        "sector": "섹터ETF"
    },
    {
        "symbol": "TLT",
        "name": "미국채 20년 ETF",
        "market": "NASDAQ",
        "sector": "채권ETF"
    },
    {
        "symbol": "IEF",
        "name": "미국채 7-10년 ETF",
        "market": "NASDAQ",
        "sector": "채권ETF"
    },
    {
        "symbol": "SHY",
        "name": "미국채 단기 ETF",
        "market": "NASDAQ",
        "sector": "채권ETF"
    },
    {
        "symbol": "HYG",
        "name": "하이일드 채권 ETF",
        "market": "NYSE",
        "sector": "채권ETF"
    },
    {
        "symbol": "TMF",
        "name": "미국채 20년 3배 레버리지",
        "market": "NYSE",
        "sector": "레버리지ETF"
    },
    {
        "symbol": "TMV",
        "name": "미국채 20년 인버스 3배",
        "market": "NYSE",
        "sector": "인버스ETF"
    },
    {
        "symbol": "GLD",
        "name": "금 ETF (GLD)",
        "market": "NYSE",
        "sector": "원자재ETF"
    },
    {
        "symbol": "IAU",
        "name": "금 ETF (IAU)",
        "market": "NYSE",
        "sector": "원자재ETF"
    },
    {
        "symbol": "SLV",
        "name": "은 ETF (SLV)",
        "market": "NYSE",
        "sector": "원자재ETF"
    },
    {
        "symbol": "PDBC",
        "name": "원자재 ETF (PDBC)",
        "market": "NASDAQ",
        "sector": "원자재ETF"
    },
    {
        "symbol": "USO",
        "name": "WTI 원유 ETF",
        "market": "NYSE",
        "sector": "원자재ETF"
    },
    {
        "symbol": "UNG",
        "name": "천연가스 ETF",
        "market": "NYSE",
        "sector": "원자재ETF"
    },
    {
        "symbol": "EWJ",
        "name": "일본 ETF (EWJ)",
        "market": "NYSE",
        "sector": "해외ETF"
    },
    {
        "symbol": "FXI",
        "name": "중국 대형주 ETF",
        "market": "NYSE",
        "sector": "해외ETF"
    },
    {
        "symbol": "KWEB",
        "name": "중국 인터넷 ETF",
        "market": "NYSE",
        "sector": "해외ETF"
    },
    {
        "symbol": "EEM",
        "name": "신흥국 ETF (EEM)",
        "market": "NYSE",
        "sector": "해외ETF"
    },
    {
        "symbol": "VEA",
        "name": "선진국 ETF (VEA)",
        "market": "NYSE",
        "sector": "해외ETF"
    },
    {
        "symbol": "INDA",
        "name": "인도 ETF (INDA)",
        "market": "NYSE",
        "sector": "해외ETF"
    },
    {
        "symbol": "EWY",
        "name": "한국 ETF (EWY)",
        "market": "NYSE",
        "sector": "해외ETF"
    },
    {
        "symbol": "UVXY",
        "name": "VIX 1.5배 레버리지",
        "market": "NASDAQ",
        "sector": "변동성ETF"
    },
    {
        "symbol": "SVXY",
        "name": "VIX 인버스 0.5배",
        "market": "NYSE",
        "sector": "변동성ETF"
    },
    {
        "symbol": "000240.KS",
        "name": "한국타이어앤테크놀로지",
        "market": "KRX",
        "sector": "자동차부품"
    },
    {
        "symbol": "090090.KQ",
        "name": "디엔에프",
        "market": "KOSDAQ",
        "sector": "반도체소재"
    },
    {
        "symbol": "007680.KS",
        "name": "팜한농",
        "market": "KRX",
        "sector": "농화학"
    },
    {
        "symbol": "000670.KS",
        "name": "영풍",
        "market": "KRX",
        "sector": "비철금속"
    },
    {
        "symbol": "005870.KS",
        "name": "휴니드",
        "market": "KRX",
        "sector": "방산"
    },
    {
        "symbol": "007660.KS",
        "name": "이수페타시스",
        "market": "KRX",
        "sector": "PCB"
    },
    {
        "symbol": "001340.KS",
        "name": "백광산업",
        "market": "KRX",
        "sector": "화학"
    },
    {
        "symbol": "034220.KS",
        "name": "LG디스플레이",
        "market": "KRX",
        "sector": "디스플레이"
    },
    {
        "symbol": "004490.KS",
        "name": "세방전지",
        "market": "KRX",
        "sector": "배터리"
    },
    {
        "symbol": "000150.KS",
        "name": "두산",
        "market": "KRX",
        "sector": "지주사"
    },
    {
        "symbol": "011780.KS",
        "name": "금호석유화학",
        "market": "KRX",
        "sector": "화학"
    },
    {
        "symbol": "000220.KS",
        "name": "유유제약",
        "market": "KRX",
        "sector": "제약"
    },
    {
        "symbol": "001800.KS",
        "name": "오리온홀딩스",
        "market": "KRX",
        "sector": "지주사"
    },
    {
        "symbol": "003960.KS",
        "name": "사조씨푸드",
        "market": "KRX",
        "sector": "식품"
    },
    {
        "symbol": "041960.KQ",
        "name": "코미팜",
        "market": "KOSDAQ",
        "sector": "바이오"
    },
    {
        "symbol": "236340.KQ",
        "name": "뷰노",
        "market": "KOSDAQ",
        "sector": "AI의료"
    },
    {
        "symbol": "228760.KQ",
        "name": "지노믹트리",
        "market": "KOSDAQ",
        "sector": "바이오"
    },
    {
        "symbol": "950160.KQ",
        "name": "코오롱티슈진",
        "market": "KOSDAQ",
        "sector": "바이오"
    },
    {
        "symbol": "108490.KQ",
        "name": "로보티즈",
        "market": "KOSDAQ",
        "sector": "로봇"
    },
    {
        "symbol": "348210.KQ",
        "name": "넥스틴",
        "market": "KOSDAQ",
        "sector": "반도체장비"
    },
    {
        "symbol": "413600.KQ",
        "name": "에이피알",
        "market": "KOSDAQ",
        "sector": "화장품"
    },
    {
        "symbol": "073490.KQ",
        "name": "어보브반도체",
        "market": "KOSDAQ",
        "sector": "반도체"
    },
    {
        "symbol": "016670.KQ",
        "name": "디지털대성",
        "market": "KOSDAQ",
        "sector": "교육"
    },
    {
        "symbol": "304100.KQ",
        "name": "솔트웨어",
        "market": "KOSDAQ",
        "sector": "AI/클라우드"
    },
    {
        "symbol": "900260.KQ",
        "name": "크리스탈지노믹스",
        "market": "KOSDAQ",
        "sector": "바이오"
    },
    {
        "symbol": "246710.KQ",
        "name": "티앤엘",
        "market": "KOSDAQ",
        "sector": "의료기기"
    },
    {
        "symbol": "319400.KQ",
        "name": "현대무벡스",
        "market": "KOSDAQ",
        "sector": "물류로봇"
    },
    {
        "symbol": "138580.KQ",
        "name": "HB테크놀러지",
        "market": "KOSDAQ",
        "sector": "반도체장비"
    },
    {
        "symbol": "460930.KQ",
        "name": "현대힘스",
        "market": "KOSDAQ",
        "sector": "조선부품"
    },
    {
        "symbol": "NVDL",
        "name": "엔비디아 2배 레버리지",
        "market": "NASDAQ",
        "sector": "레버리지ETF"
    },
    {
        "symbol": "TSLL",
        "name": "테슬라 2배 레버리지",
        "market": "NASDAQ",
        "sector": "레버리지ETF"
    },
    {
        "symbol": "MSFO",
        "name": "마이크로소프트 커버드콜",
        "market": "NASDAQ",
        "sector": "ETF"
    },
    {
        "symbol": "SPYI",
        "name": "S&P500 인컴 ETF",
        "market": "NYSE",
        "sector": "ETF"
    },
    {
        "symbol": "JEPI",
        "name": "JP모건 인컴 ETF",
        "market": "NYSE",
        "sector": "ETF"
    },
    {
        "symbol": "JEPQ",
        "name": "JP모건 나스닥 인컴 ETF",
        "market": "NASDAQ",
        "sector": "ETF"
    },
    {
        "symbol": "QYLD",
        "name": "나스닥100 커버드콜 ETF",
        "market": "NASDAQ",
        "sector": "ETF"
    },
    {
        "symbol": "XYLD",
        "name": "S&P500 커버드콜 ETF",
        "market": "NYSE",
        "sector": "ETF"
    },
    {
        "symbol": "RYLD",
        "name": "러셀2000 커버드콜 ETF",
        "market": "NYSE",
        "sector": "ETF"
    },
    {
        "symbol": "SCHD",
        "name": "배당성장 ETF (SCHD)",
        "market": "NYSE",
        "sector": "배당ETF"
    },
    {
        "symbol": "VIG",
        "name": "배당성장 ETF (VIG)",
        "market": "NYSE",
        "sector": "배당ETF"
    },
    {
        "symbol": "VYM",
        "name": "고배당 ETF (VYM)",
        "market": "NYSE",
        "sector": "배당ETF"
    },
    {
        "symbol": "DVY",
        "name": "배당 ETF (DVY)",
        "market": "NASDAQ",
        "sector": "배당ETF"
    },
    {
        "symbol": "HDV",
        "name": "배당 ETF (HDV)",
        "market": "NYSE",
        "sector": "배당ETF"
    },
    {
        "symbol": "NOBL",
        "name": "배당귀족 ETF",
        "market": "NYSE",
        "sector": "배당ETF"
    },
    {
        "symbol": "VTI",
        "name": "미국전체시장 ETF (VTI)",
        "market": "NYSE",
        "sector": "ETF"
    },
    {
        "symbol": "VT",
        "name": "글로벌전체시장 ETF",
        "market": "NYSE",
        "sector": "ETF"
    },
    {
        "symbol": "ACWI",
        "name": "MSCI 전세계 ETF",
        "market": "NASDAQ",
        "sector": "해외ETF"
    },
    {
        "symbol": "EFA",
        "name": "선진국 ETF (EFA)",
        "market": "NYSE",
        "sector": "해외ETF"
    },
    {
        "symbol": "EWG",
        "name": "독일 ETF",
        "market": "NYSE",
        "sector": "해외ETF"
    },
    {
        "symbol": "EWU",
        "name": "영국 ETF",
        "market": "NYSE",
        "sector": "해외ETF"
    },
    {
        "symbol": "EWA",
        "name": "호주 ETF",
        "market": "NYSE",
        "sector": "해외ETF"
    },
    {
        "symbol": "EWZ",
        "name": "브라질 ETF",
        "market": "NYSE",
        "sector": "해외ETF"
    },
    {
        "symbol": "RSX",
        "name": "러시아 ETF",
        "market": "NYSE",
        "sector": "해외ETF"
    },
    {
        "symbol": "GXC",
        "name": "중국 전체 ETF",
        "market": "NYSE",
        "sector": "해외ETF"
    },
    {
        "symbol": "MCHI",
        "name": "MSCI 중국 ETF",
        "market": "NASDAQ",
        "sector": "해외ETF"
    },
    {
        "symbol": "CQQQ",
        "name": "중국 기술주 ETF",
        "market": "NASDAQ",
        "sector": "해외ETF"
    },
    {
        "symbol": "INCO",
        "name": "인도 소비자 ETF",
        "market": "NYSE",
        "sector": "해외ETF"
    },
    {
        "symbol": "VNM",
        "name": "베트남 ETF",
        "market": "NYSE",
        "sector": "해외ETF"
    },
    {
        "symbol": "DBA",
        "name": "농산물 ETF",
        "market": "NASDAQ",
        "sector": "원자재ETF"
    },
    {
        "symbol": "CORN",
        "name": "옥수수 ETF",
        "market": "NASDAQ",
        "sector": "원자재ETF"
    },
    {
        "symbol": "WEAT",
        "name": "밀 ETF",
        "market": "NYSE",
        "sector": "원자재ETF"
    },
    {
        "symbol": "CPER",
        "name": "구리 ETF",
        "market": "NYSE",
        "sector": "원자재ETF"
    },
    {
        "symbol": "PALL",
        "name": "팔라듐 ETF",
        "market": "NYSE",
        "sector": "원자재ETF"
    },
    {
        "symbol": "PPLT",
        "name": "플래티넘 ETF",
        "market": "NYSE",
        "sector": "원자재ETF"
    },
    {
        "symbol": "URA",
        "name": "우라늄 ETF",
        "market": "NYSE",
        "sector": "원자재ETF"
    },
    {
        "symbol": "URNM",
        "name": "우라늄 채굴 ETF",
        "market": "NASDAQ",
        "sector": "섹터ETF"
    },
    {
        "symbol": "NLR",
        "name": "원자력 ETF",
        "market": "NYSE",
        "sector": "섹터ETF"
    },
    {
        "symbol": "REMX",
        "name": "희토류/전략광물 ETF",
        "market": "NYSE",
        "sector": "원자재ETF"
    },
    {
        "symbol": "COPX",
        "name": "구리 채굴 ETF",
        "market": "NYSE",
        "sector": "섹터ETF"
    },
    {
        "symbol": "GDX",
        "name": "금 채굴 ETF",
        "market": "NYSE",
        "sector": "섹터ETF"
    },
    {
        "symbol": "GDXJ",
        "name": "소형 금 채굴 ETF",
        "market": "NYSE",
        "sector": "섹터ETF"
    },
    {
        "symbol": "SIL",
        "name": "은 채굴 ETF",
        "market": "NYSE",
        "sector": "섹터ETF"
    },
    {
        "symbol": "IBIT",
        "name": "블랙록 비트코인 ETF",
        "market": "NASDAQ",
        "sector": "가상자산ETF"
    },
    {
        "symbol": "FBTC",
        "name": "피델리티 비트코인 ETF",
        "market": "NYSE",
        "sector": "가상자산ETF"
    },
    {
        "symbol": "GBTC",
        "name": "그레이스케일 비트코인",
        "market": "NYSE",
        "sector": "가상자산ETF"
    },
    {
        "symbol": "ETHA",
        "name": "블랙록 이더리움 ETF",
        "market": "NASDAQ",
        "sector": "가상자산ETF"
    },
    {
        "symbol": "RIOT",
        "name": "라이엇플랫폼스",
        "market": "NASDAQ",
        "sector": "비트코인채굴"
    },
    {
        "symbol": "MARA",
        "name": "마라홀딩스",
        "market": "NASDAQ",
        "sector": "비트코인채굴"
    },
    {
        "symbol": "CLSK",
        "name": "클린스파크",
        "market": "NASDAQ",
        "sector": "비트코인채굴"
    },
    {
        "symbol": "AAON",
        "name": "AAON Inc",
        "market": "NASDAQ",
        "sector": "산업재"
    },
    {
        "symbol": "APP",
        "name": "AppLovin",
        "market": "NASDAQ",
        "sector": "AI/광고"
    },
    {
        "symbol": "APLS",
        "name": "어펠리스테라퓨틱스",
        "market": "NASDAQ",
        "sector": "바이오"
    },
    {
        "symbol": "AXON",
        "name": "액슨엔터프라이즈",
        "market": "NASDAQ",
        "sector": "방산/AI"
    },
    {
        "symbol": "CELH",
        "name": "셀시우스홀딩스",
        "market": "NASDAQ",
        "sector": "식음료"
    },
    {
        "symbol": "DECK",
        "name": "데커스아웃도어",
        "market": "NYSE",
        "sector": "소비재"
    },
    {
        "symbol": "ELF",
        "name": "e.l.f뷰티",
        "market": "NYSE",
        "sector": "화장품"
    },
    {
        "symbol": "EXAS",
        "name": "익그젝트사이언스",
        "market": "NASDAQ",
        "sector": "바이오"
    },
    {
        "symbol": "FICO",
        "name": "페어아이작",
        "market": "NYSE",
        "sector": "소프트웨어"
    },
    {
        "symbol": "GEV",
        "name": "GE버노바",
        "market": "NYSE",
        "sector": "에너지"
    },
    {
        "symbol": "GWAV",
        "name": "그린웨이브테크",
        "market": "NASDAQ",
        "sector": "재활용"
    },
    {
        "symbol": "HWM",
        "name": "하웨트",
        "market": "NYSE",
        "sector": "항공"
    },
    {
        "symbol": "IOT",
        "name": "센티넬원",
        "market": "NYSE",
        "sector": "사이버보안"
    },
    {
        "symbol": "LUNR",
        "name": "인튜이티브머신스",
        "market": "NASDAQ",
        "sector": "우주"
    },
    {
        "symbol": "RKLB",
        "name": "로켓랩",
        "market": "NASDAQ",
        "sector": "우주"
    },
    {
        "symbol": "SPCE",
        "name": "버진갤럭틱",
        "market": "NYSE",
        "sector": "우주"
    },
    {
        "symbol": "ASTS",
        "name": "AST스페이스모바일",
        "market": "NASDAQ",
        "sector": "우주통신"
    },
    {
        "symbol": "ACHR",
        "name": "아처에비에이션",
        "market": "NYSE",
        "sector": "에어모빌리티"
    },
    {
        "symbol": "JOBY",
        "name": "조비에비에이션",
        "market": "NYSE",
        "sector": "에어모빌리티"
    },
    {
        "symbol": "LILM",
        "name": "릴리움",
        "market": "NASDAQ",
        "sector": "에어모빌리티"
    },
    {
        "symbol": "NKLA",
        "name": "니콜라",
        "market": "NASDAQ",
        "sector": "수소트럭"
    },
    {
        "symbol": "HYLN",
        "name": "하일리온",
        "market": "NASDAQ",
        "sector": "전기트럭"
    },
    {
        "symbol": "WKHS",
        "name": "워크호스그룹",
        "market": "NASDAQ",
        "sector": "전기트럭"
    },
    {
        "symbol": "FSR",
        "name": "피스커",
        "market": "NYSE",
        "sector": "전기차"
    },
    {
        "symbol": "GOEV",
        "name": "카누",
        "market": "NASDAQ",
        "sector": "전기차"
    },
    {
        "symbol": "BLNK",
        "name": "블링크차징",
        "market": "NASDAQ",
        "sector": "EV충전"
    },
    {
        "symbol": "CHPT",
        "name": "차지포인트",
        "market": "NYSE",
        "sector": "EV충전"
    },
    {
        "symbol": "EVGO",
        "name": "이브고",
        "market": "NASDAQ",
        "sector": "EV충전"
    },
    {
        "symbol": "BE",
        "name": "블룸에너지",
        "market": "NYSE",
        "sector": "수소연료전지"
    },
    {
        "symbol": "PLUG",
        "name": "플러그파워",
        "market": "NASDAQ",
        "sector": "수소"
    },
    {
        "symbol": "FCEL",
        "name": "퓨얼셀에너지",
        "market": "NASDAQ",
        "sector": "수소연료전지"
    },
    {
        "symbol": "STEM",
        "name": "스템에너지",
        "market": "NYSE",
        "sector": "에너지저장"
    },
    {
        "symbol": "ARRY",
        "name": "어레이테크놀로지스",
        "market": "NASDAQ",
        "sector": "태양광"
    },
    {
        "symbol": "NOVA",
        "name": "선노바에너지",
        "market": "NYSE",
        "sector": "태양광"
    },
    {
        "symbol": "SEDG",
        "name": "솔라엣지테크",
        "market": "NASDAQ",
        "sector": "태양광"
    },
    {
        "symbol": "ORA",
        "name": "오르마트테크",
        "market": "NYSE",
        "sector": "지열에너지"
    },
    {
        "symbol": "HIMS",
        "name": "힘스앤허스",
        "market": "NYSE",
        "sector": "헬스케어"
    },
    {
        "symbol": "TDOC",
        "name": "텔라닥헬스",
        "market": "NYSE",
        "sector": "원격의료"
    },
    {
        "symbol": "AMWL",
        "name": "아메리칸웰",
        "market": "NYSE",
        "sector": "원격의료"
    },
    {
        "symbol": "ACAD",
        "name": "ACADIA파마",
        "market": "NASDAQ",
        "sector": "바이오"
    },
    {
        "symbol": "ARWR",
        "name": "애로우헤드파마",
        "market": "NASDAQ",
        "sector": "바이오"
    },
    {
        "symbol": "BEAM",
        "name": "빔테라퓨틱스",
        "market": "NASDAQ",
        "sector": "유전자편집"
    },
    {
        "symbol": "CRSP",
        "name": "크리스퍼테라퓨틱스",
        "market": "NASDAQ",
        "sector": "유전자편집"
    },
    {
        "symbol": "EDIT",
        "name": "에디타스메디신",
        "market": "NASDAQ",
        "sector": "유전자편집"
    },
    {
        "symbol": "NTLA",
        "name": "인텔리아테라퓨틱스",
        "market": "NASDAQ",
        "sector": "유전자편집"
    },
    {
        "symbol": "PACB",
        "name": "퍼시픽바이오사이언스",
        "market": "NASDAQ",
        "sector": "바이오"
    },
    {
        "symbol": "RXRX",
        "name": "레커시브파마",
        "market": "NASDAQ",
        "sector": "AI바이오"
    },
    {
        "symbol": "SDGR",
        "name": "슈뢰딩거",
        "market": "NASDAQ",
        "sector": "AI바이오"
    },
    {
        "symbol": "TWST",
        "name": "트위스트바이오사이언스",
        "market": "NASDAQ",
        "sector": "합성생물학"
    },
    {
        "symbol": "SSEM.KS",
        "name": "삼성전자 2X 레버리지 ETN",
        "market": "KRX",
        "sector": "레버리지ETN"
    },
    {
        "symbol": "579200.KS",
        "name": "삼성전자 2배레버리지 ETN(H)",
        "market": "KRX",
        "sector": "레버리지ETN"
    },
    {
        "symbol": "580048.KS",
        "name": "KODEX 삼성전자레버리지",
        "market": "KRX",
        "sector": "레버리지ETF"
    },
    {
        "symbol": "266390.KS",
        "name": "KODEX 코스피레버리지",
        "market": "KRX",
        "sector": "레버리지ETF"
    },
    {
        "symbol": "122630.KS",
        "name": "KODEX 레버리지",
        "market": "KRX",
        "sector": "레버리지ETF"
    },
    {
        "symbol": "114800.KS",
        "name": "KODEX 인버스",
        "market": "KRX",
        "sector": "인버스ETF"
    },
    {
        "symbol": "252670.KS",
        "name": "KODEX 200선물인버스2X",
        "market": "KRX",
        "sector": "인버스ETF"
    },
    {
        "symbol": "233740.KS",
        "name": "KODEX 코스닥150레버리지",
        "market": "KRX",
        "sector": "레버리지ETF"
    },
    {
        "symbol": "251340.KS",
        "name": "KODEX 코스닥150인버스",
        "market": "KRX",
        "sector": "인버스ETF"
    },
    {
        "symbol": "278530.KS",
        "name": "KODEX 반도체레버리지",
        "market": "KRX",
        "sector": "레버리지ETF"
    },
    {
        "symbol": "261250.KS",
        "name": "KODEX MSCI한국레버리지",
        "market": "KRX",
        "sector": "레버리지ETF"
    },
    {
        "symbol": "243890.KS",
        "name": "TIGER 200 IT레버리지",
        "market": "KRX",
        "sector": "레버리지ETF"
    },
    {
        "symbol": "367380.KS",
        "name": "TIGER 2차전지테마레버리지",
        "market": "KRX",
        "sector": "레버리지ETF"
    },
    {
        "symbol": "462900.KS",
        "name": "TIGER 삼성그룹레버리지",
        "market": "KRX",
        "sector": "레버리지ETF"
    }
]

GRADE_INFO = {
    "A": {"label": "[공시원문]", "color": "🟢", "desc": "1차 소스(DART/SEC 직접 수집)"},
    "B": {"label": "[포털]", "color": "🔵", "desc": "2개 이상 소스 교차 검증"},
    "C": {"label": "[단일출처]", "color": "🟡", "desc": "단일 출처, 미검증"},
    "D": {"label": "[-]", "color": "⚫", "desc": "검증 불가"},
}


def format_grade(grade: str) -> str:
    info = GRADE_INFO.get(grade, GRADE_INFO["D"])
    return f"{info['color']} {info['label']}"


def get_stock_info(symbol: str) -> dict:
    """주가 정보 조회 (yfinance)"""
    try:
        ticker = yf.Ticker(symbol)
        info   = ticker.info

        # info가 비어있거나 quoteType이 없으면 history로 대체 시도
        price = (
            info.get("currentPrice") or
            info.get("regularMarketPrice") or
            info.get("previousClose")
        )

        # price가 여전히 없으면 history에서 직접 가져오기
        if price is None or (isinstance(price, float) and str(price) == "nan"):
            hist = get_historical_data(symbol, "5d")
            if hist is not None and not hist.empty and "Close" in hist.columns:
                price = float(hist["Close"].iloc[-1])

        currency   = info.get("currency", "KRW" if symbol.endswith(".KS") else "USD")
        prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose") or 0

        change     = round(float(price or 0) - float(prev_close or 0), 2) if price else None
        change_pct = round((change / float(prev_close) * 100), 2) if prev_close and change is not None else None

        def safe_float(val):
            """NaN, None, inf 처리"""
            if val is None:
                return None
            try:
                f = float(val)
                if str(f) in ("nan", "inf", "-inf"):
                    return None
                return f
            except Exception:
                return None

        return {
            "symbol":    symbol,
            "name":      info.get("shortName") or info.get("longName") or symbol,
            "currency":  currency,
            "currentPrice":  {"value": safe_float(price),      "grade": "B", "source": "yfinance"},
            "changeAmount":  {"value": safe_float(change),     "grade": "B", "source": "yfinance"},
            "changePercent": {"value": safe_float(change_pct), "grade": "B", "source": "yfinance"},
            "volume":    {"value": safe_float(info.get("volume")),      "grade": "B", "source": "yfinance"},
            "marketCap": {"value": safe_float(info.get("marketCap")),   "grade": "B", "source": "yfinance"},
            "per":       {"value": safe_float(info.get("trailingPE")),  "grade": "B", "source": "yfinance"},
            "pbr":       {"value": safe_float(info.get("priceToBook")), "grade": "B", "source": "yfinance"},
            "eps":       {"value": safe_float(info.get("trailingEps")), "grade": "B", "source": "yfinance"},
            "dividendYield": {
                "value": round(safe_float(info.get("dividendYield")) * 100, 2)
                         if safe_float(info.get("dividendYield")) else None,
                "grade": "B", "source": "yfinance",
            },
            "week52High": {"value": safe_float(info.get("fiftyTwoWeekHigh")), "grade": "B", "source": "yfinance"},
            "week52Low":  {"value": safe_float(info.get("fiftyTwoWeekLow")),  "grade": "B", "source": "yfinance"},
            "sector":      info.get("sector", ""),
            "industry":    info.get("industry", ""),
            "description": info.get("longBusinessSummary", ""),
            "employees":   info.get("fullTimeEmployees"),
            "website":     info.get("website", ""),
        }

    except Exception as e:
        return {"symbol": symbol, "name": symbol, "error": str(e)}

def get_historical_data(symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
    """주가 히스토리 데이터 조회"""
    try:
        ticker = yf.Ticker(symbol)
        hist   = ticker.history(period=period)

        if hist.empty:
            return None

        # MultiIndex 컬럼이면 단순 컬럼으로 변환
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = [col[0] for col in hist.columns]

        # 타임존 제거
        if hasattr(hist.index, "tz") and hist.index.tz is not None:
            hist.index = hist.index.tz_localize(None)

        return hist
    except Exception:
        return None


def get_macro_data() -> dict:
    """거시경제 지표 조회"""
    results = {}
    macro_symbols = {
        "KOSPI":        "^KS11",
        "KOSDAQ":       "^KQ11",
        "S&P 500":      "^GSPC",
        "NASDAQ":       "^IXIC",
        "USD/KRW":      "KRW=X",
        "DXY":          "DX-Y.NYB",
        "미국 국채 10년물": "^TNX",
        "금 (Gold)":    "GC=F",
        "WTI 원유":     "CL=F",
    }
    for name, sym in macro_symbols.items():
        try:
            ticker = yf.Ticker(sym)
            hist   = ticker.history(period="5d")

            if hist.empty:
                results[name] = {"symbol": sym, "value": None, "grade": "D"}
                continue

            # ── MultiIndex 컬럼 대응 ──────────────────────────
            # yfinance 최신 버전에서 컬럼이 ("Close", "^KS11") 형태로 올 수 있음
            close_col = None
            for col in hist.columns:
                col_str = col[0] if isinstance(col, tuple) else col
                if col_str == "Close":
                    close_col = col
                    break

            if close_col is None:
                results[name] = {"symbol": sym, "value": None, "grade": "D"}
                continue

            close = hist[close_col].dropna()
            if close.empty:
                results[name] = {"symbol": sym, "value": None, "grade": "D"}
                continue

            last = float(close.iloc[-1])
            prev = float(close.iloc[-2]) if len(close) > 1 else last
            chg      = last - prev
            chg_pct  = (chg / prev * 100) if prev else 0

            results[name] = {
                "symbol":    sym,
                "value":     round(last, 2),
                "change":    round(chg, 2),
                "changePct": round(chg_pct, 2),
                "grade":     "B",
                "source":    "Yahoo Finance",
            }
        except Exception as e:
            results[name] = {"symbol": sym, "value": None, "grade": "D"}

    return results


def search_stocks(query: str) -> list[dict]:
    """종목 검색"""
    query_lower = query.lower()
    results = [
        s for s in POPULAR_STOCKS
        if query_lower in s["symbol"].lower() or query_lower in s["name"].lower()
    ]
    if not results:
        try:
            sym = query.upper()
            ticker = yf.Ticker(sym)
            info = ticker.info
            if info.get("shortName"):
                results.append({
                    "symbol": sym,
                    "name": info["shortName"],
                    "market": info.get("exchange", "UNKNOWN"),
                })
        except Exception:
            pass
    return results[:20]
