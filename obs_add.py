import sys
import urllib.request
import urllib.parse
import json

# =========================
# 設定
# =========================
SERVER_URL = "http://127.0.0.1:8787/add"


def main():
    if len(sys.argv) < 3:
        print("使い方: python obs_add.py <名前> <pt>")
        sys.exit(1)

    name = sys.argv[1]
    pt = sys.argv[2]

    if not pt.isdigit():
        print("pt は数字で指定してください")
        sys.exit(1)

    data = urllib.parse.urlencode({
        "name": name,
        "pt": pt
    }).encode("utf-8")

    req = urllib.request.Request(
        SERVER_URL,
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            body = res.read().decode("utf-8")
            print("OK:", body)
    except Exception as e:
        print("ERROR:", e)


if __name__ == "__main__":
    main()
