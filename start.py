"""
투자 내비게이터 v2.0 — 통합 실행 스크립트
사용법: python start.py

Flask  백엔드: http://localhost:5001
React  프론트: http://localhost:5173
"""
import subprocess, sys, os, time, signal, threading

# ── .env 파일 로드 ────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv 미설치 시 무시

# ── CLOVA API 키 없으면 최초 1회 입력 요청 ───────────────
if not os.environ.get("CLOVA_API_KEY"):
    print("=" * 55)
    print("  CLOVA Studio API 키를 입력해주세요.")
    print("  발급: https://console.ncloud.com → CLOVA Studio")
    print("  (엔터만 누르면 KNU 감성사전으로 대체됩니다)")
    print("=" * 55)
    key = input("  API 키: ").strip()
    if key:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
                  "w", encoding="utf-8") as _f:
            _f.write(f"CLOVA_API_KEY={key}\n")
        os.environ["CLOVA_API_KEY"] = key
        print("  저장 완료! 다음부터는 자동으로 불러옵니다.")
    else:
        print("  키 미입력 → KNU 감성사전으로 동작합니다.")

BASE = os.path.dirname(os.path.abspath(__file__))
FLASK_PORT     = 5001
REACT_PORT     = 5173
procs = []

# ── Node.js 설치 확인 ─────────────────────────────────────
def _check_node():
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    try:
        result = subprocess.run(
            [npm_cmd, "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return npm_cmd
        raise FileNotFoundError
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("=" * 55)
        print("  Node.js가 설치되어 있지 않습니다.")
        print()
        print("  아래 주소에서 Node.js LTS 버전을 설치해주세요:")
        print("  https://nodejs.org/ko")
        print()
        print("  설치 완료 후 PyCharm을 재시작하고")
        print("  다시 실행 버튼을 눌러주세요.")
        print("=" * 55)
        sys.exit(1)

# ── npm install 자동 실행 (최초 1회) ──────────────────────
def _ensure_npm_packages(npm_cmd):
    frontend_dir = os.path.join(BASE, "invest-nav-frontend")
    node_modules = os.path.join(frontend_dir, "node_modules")

    if not os.path.exists(node_modules):
        print("=" * 55)
        print("  React 패키지 설치 중... (최초 1회, 1~3분 소요)")
        print("  잠시 기다려주세요.")
        print("=" * 55)
        result = subprocess.run(
            [npm_cmd, "install"],
            cwd=frontend_dir,
        )
        if result.returncode != 0:
            print("  npm install 실패. 아래 명령어를 직접 실행해주세요:")
            print("  cd invest-nav-frontend && npm install")
            sys.exit(1)
        print("  패키지 설치 완료!")
    else:
        print("  Node.js 패키지 확인 완료")



def _stream(proc, prefix):
    for line in proc.stdout:
        print(f"[{prefix}] {line}", end="")


def _start_flask():
    env = os.environ.copy()
    env["FLASK_PORT"] = str(FLASK_PORT)
    p = subprocess.Popen(
        [sys.executable, "backend/app.py"],
        cwd=BASE, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
        encoding="utf-8",   # ← 추가
        errors="replace",   # ← 추가 (변환 불가 문자는 ?로 대체)
    )
    procs.append(p)
    threading.Thread(target=_stream, args=(p, "Flask"), daemon=True).start()
    return p


def _start_react():
    """React 개발 서버 실행 (invest-nav-frontend 폴더)"""
    frontend_dir = os.path.join(BASE, "invest-nav-frontend")
    # npm이 없으면 안내 출력
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    p = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=frontend_dir,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
        encoding="utf-8",
        errors="replace",
    )
    procs.append(p)
    threading.Thread(target=_stream, args=(p, "React"), daemon=True).start()
    return p


def _shutdown(sig, frame):
    print("\n[start.py] 종료 신호 수신 — 두 서버를 종료합니다...")
    for p in procs:
        try: p.terminate()
        except: pass
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    print("=" * 55)
    print("  투자 내비게이터 v2.0  |  Flask + React")
    print("=" * 55)

    # 1. Node.js 설치 확인
    npm_cmd = _check_node()

    # 2. npm install 자동 실행 (최초 1회)
    _ensure_npm_packages(npm_cmd)

    print(f"  Flask  API : http://localhost:{FLASK_PORT}")
    print(f"  React  앱  : http://localhost:{REACT_PORT}")
    print("  종료: Ctrl + C")
    print("=" * 55)

    # 3. Flask 백엔드 시작
    flask_p = _start_flask()
    print("[start.py] Flask 백엔드 시작 중... (3초 대기)")
    time.sleep(3)

    # 4. React 프론트엔드 시작
    react_p = _start_react()
    print("[start.py] React 프론트엔드 시작 중...")
    print(f"[start.py] 브라우저에서 http://localhost:{REACT_PORT} 를 열어주세요.")

    try:
        flask_p.wait()
    except KeyboardInterrupt:
        _shutdown(None, None)
