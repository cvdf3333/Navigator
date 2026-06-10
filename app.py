import sys
import os

# 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from backend.app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)