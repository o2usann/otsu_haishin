from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import subprocess
import os
import threading
import twitch_chat

PORT = 8787
DATA_FILE = "points.json"
JST = ZoneInfo("Asia/Tokyo")
CHAT_DELAY_SEC = 60

def now_str():
    return datetime.now(JST).strftime("%H:%M:%S")

def load_points_dict():
    if not os.path.exists(DATA_FILE):
        return {"log": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("log"), list):
            return data
        return {"log": []}
    except Exception:
        return {"log": []}

def save_points_dict(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_point(name: str, pt: int):
    data = load_points_dict()
    data.setdefault("log", []).append({
        "name": name,
        "pt": pt,
        "ts": datetime.now(JST).isoformat()
    })
    save_points_dict(data)

def render_site():
    subprocess.run(["python", "render_site.py"], check=False)

def git_autopush_docs_only():
    """
    docs/ に変更があるときだけ commit & push（失敗は表示）
    """
    st = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if not st.stdout.strip():
        return

    subprocess.run(["git", "add", "docs"], check=False)
    subprocess.run(["git", "commit", "-m", "auto update"], check=False)

    p = subprocess.run(["git", "push"], capture_output=True, text=True)
    if p.returncode == 0:
        print("[git] pushed")
    else:
        print("[git] push failed")
        if p.stderr:
            print(p.stderr.strip())

def send_chat_later(name: str, pt: int):
    def _task():
        url = os.getenv("GRAPH_URL", "").strip()
        msg = f"{name} さんから {pt} ptの感謝！！  ランキングはこちらから {url}"
        ok, reason = twitch_chat.send_chat_message(msg)
        print(f"[{now_str()}] CHAT: {'sent' if ok else 'failed'} ({reason})")
    threading.Timer(CHAT_DELAY_SEC, _task).start()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        return

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path != "/add":
            self.send_response(404)
            self._cors()
            self.end_headers()
            return

        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        ctype = (self.headers.get("Content-Type") or "").lower()

        name = ""
        pt = 0

        try:
            if "application/json" in ctype:
                obj = json.loads(raw.decode("utf-8"))
                name = str(obj.get("name", "")).strip()
                pt = int(obj.get("pt", 0))
            else:
                p = urllib.parse.parse_qs(raw.decode("utf-8"))
                name = p.get("name", [""])[0].strip()
                pt = int(p.get("pt", ["0"])[0])
        except Exception:
            name = ""
            pt = 0

        if not name or pt <= 0:
            self.send_response(400)
            self._cors()
            self.end_headers()
            return

        add_point(name, pt)
        render_site()
        git_autopush_docs_only()
        send_chat_later(name, pt)

        print(f"[{now_str()}] ADD {name} +{pt}pt")

        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}, ensure_ascii=False).encode("utf-8"))

if __name__ == "__main__":
    print(f"Server: http://127.0.0.1:{PORT}/add")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
