import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from backend.app import app
from flask import send_from_directory, send_file

# dist 폴더 경로
DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")

@app.route("/")
def serve_index():
    return send_file(os.path.join(DIST_DIR, "index.html"))

@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(os.path.join(DIST_DIR, "assets"), filename)

@app.route("/<path:path>")
def serve_static(path):
    file_path = os.path.join(DIST_DIR, path)
    if os.path.exists(file_path):
        return send_from_directory(DIST_DIR, path)
    return send_file(os.path.join(DIST_DIR, "index.html"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)