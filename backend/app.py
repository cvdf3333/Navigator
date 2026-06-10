"""
투자 내비게이터 v2.0 — Flask 백엔드
실행: python backend/app.py   (또는 start.py 로 통합 실행)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_cors import CORS

from routes.macro       import macro_bp
from routes.stocks      import stocks_bp
from routes.news        import news_bp
from routes.disclosure  import disclosure_bp
from routes.portfolio   import portfolio_bp
from routes.memo        import memo_bp

app = Flask(__name__)
CORS(app)   # Streamlit → Flask 크로스오리진 허용

app.register_blueprint(macro_bp,      url_prefix="/api/macro")
app.register_blueprint(stocks_bp,     url_prefix="/api/stocks")
app.register_blueprint(news_bp,       url_prefix="/api/news")
app.register_blueprint(disclosure_bp, url_prefix="/api/disclosure")
app.register_blueprint(portfolio_bp,  url_prefix="/api/portfolio")
app.register_blueprint(memo_bp,       url_prefix="/api/memo")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "투자 내비게이터 Flask API"}


if __name__ == "__main__":
    import logging
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)  # WARNING 이하 메시지 숨김

    port = int(os.environ.get("FLASK_PORT", 5001))
    print(f"[Flask] 백엔드 API 서버 시작: http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
