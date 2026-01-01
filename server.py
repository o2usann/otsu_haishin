from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import subprocess
import os
import twitch_chat


# =========================
# 設定
# =========================
PORT = 8787
DATA_FILE = "points.json"
SITE_DIR = "docs"
JST = ZoneInfo("Asia/Tokyo")

# =========================
# 共通関数
# =========================
def now_str():
    """JSTで HH:MM:SS を返す"""
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
    data["log"].append({
        "name": name,
        "pt": pt,
        "ts": datetime.now(JST).isoformat()
    })
    save_points_dict(data)


def render_site():
    # 集計HTML再生成
    subprocess.run(["python", "render_site.py"], check=False)


# =========================
# HTTP Handler
# =========================
class Handler(BaseHTTPRequestHandler):

    # ---- 余計なアクセスログを消す ----
    def log_message(self, format, *args):
        return

    # ---- CORS ----
    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    # ---- GET ----
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"OK")
            return

        self.send_response(404)
        self._set_cors_headers()
        self.end_headers()

    # ---- OPTIONS (CORS preflight) ----
    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    # ---- POST /add ----
    def do_POST(self):
        if self.path != "/add":
            self.send_response(404)
            self._set_cors_headers()
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        ctype = (self.headers.get("Content-Type") or "").lower()

        name = ""
        pt_str = "0"

        # JSON or form
        if "application/json" in ctype:
            try:
                obj = json.loads(raw.decode("utf-8"))
                name = str(obj.get("name", "")).strip()
                pt_str = str(obj.get("pt", "0")).strip()
            except Exception:
                pass
        else:
            body = raw.decode("utf-8")
            params = urllib.parse.parse_qs(body)
            name = params.get("name", [""])[0].strip()
            pt_str = params.get("pt", ["0"])[0].strip()

        # validation
        if not name or not pt_str.isdigit():
            self.send_response(400)
            self._set_cors_headers()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"invalid")
            return

        pt = int(pt_str)

        # 追加＆再生成
        add_point(name, pt)
        render_site()

        # Twitchチャットへ通知（失敗しても処理は続ける）
        graph_url = os.getenv("GRAPH_URL", "").strip()
        msg = f"応援ポイントが送られました！！（{name} +{pt}） 累計グラフを確認しよう！ {graph_url}"
        ok, reason = twitch_chat.send_chat_message(msg)
        if ok:
            print(f"[{datetime.now(JST).strftime('%H:%M:%S')}] CHAT: sent")
        else:
            print(f"[{datetime.now(JST).strftime('%H:%M:%S')}] CHAT: failed ({reason})")


        # ---- 分かりやすいログ ----
        print(f"[{now_str()}] ADD {name} +{pt}pt")

        # ---- 応答 ----
        self.send_response(200)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok",
            "name": name,
            "pt": pt
        }, ensure_ascii=False).encode("utf-8"))


# =========================
# 起動
# =========================
if __name__ == "__main__":
    print(f"Server: http://127.0.0.1:{PORT}/  POST /add")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
