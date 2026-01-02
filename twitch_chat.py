# twitch_chat.py
import os
import ssl
import socket
import time

HOST = "irc.chat.twitch.tv"
PORT = 6697  # SSL IRC

def _send(sock, msg: str):
    sock.send((msg + "\r\n").encode("utf-8"))

def send_chat_message(message: str, timeout_sec: float = 3.0):

    nick = (os.getenv("TWITCH_BOT_NICK") or "").strip().lower()
    oauth = (os.getenv("TWITCH_BOT_OAUTH") or "").strip()
    channel = (os.getenv("TWITCH_CHANNEL") or "").strip().lower().lstrip("#")


    if not nick or not oauth or not channel:
        return False, "env_missing"

    # PASS は oauth: 付きが必要。無ければ付ける
    if not oauth.startswith("oauth:"):
        oauth = "oauth:" + oauth

    ctx = ssl.create_default_context()
    raw = socket.create_connection((HOST, PORT), timeout=timeout_sec)
    sock = ctx.wrap_socket(raw, server_hostname=HOST)

    try:
        _send(sock, f"PASS {oauth}")
        _send(sock, f"NICK {nick}")
        _send(sock, f"JOIN #{channel}")

        # JOIN 完了 & PING 対応をちょい待つ
        sock.settimeout(0.3)
        end = time.time() + 1.5
        joined = False

        while time.time() < end:
            try:
                data = sock.recv(4096).decode("utf-8", errors="ignore")
            except Exception:
                break
            if not data:
                break

            for line in data.split("\r\n"):
                if not line:
                    continue
                if line.startswith("PING "):
                    _send(sock, "PONG " + line.split(" ", 1)[1])
                # 典型: ":tmi.twitch.tv 001 <nick> :Welcome, GLHF!"
                if " 001 " in line:
                    joined = True
                # JOIN 成功の行が来ることもある
                if f"JOIN #{channel}" in line:
                    joined = True

            if joined:
                break

        # メッセージ送信
        _send(sock, f"PRIVMSG #{channel} :{message}")
        return True, "ok"

    except Exception as e:
        return False, f"exception:{type(e).__name__}"
    finally:
        try:
            sock.close()
        except Exception:
            pass
