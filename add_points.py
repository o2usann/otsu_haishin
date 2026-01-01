import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

BASE = Path(__file__).parent
DATA = BASE / "points.json"
JST = ZoneInfo("Asia/Tokyo")

def load():
    if DATA.exists():
        return json.loads(DATA.read_text(encoding="utf-8"))
    return {"log": []}

def save(data: dict):
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    name = input("名前: ").strip()
    if not name:
        print("名前が空です")
        return

    pt_str = input("pt: ").strip()
    try:
        pt = int(pt_str)
    except ValueError:
        print("ptは整数で入力してね")
        return
    if pt <= 0:
        print("ptは正の整数で入力してね")
        return

    data = load()
    ts = datetime.now(JST).isoformat(timespec="seconds")

    data["log"].append({
        "ts": ts,     # 例: 2026-01-01T21:10:00+09:00
        "name": name,
        "pt": pt
    })

    save(data)
    print(f"OK: {name} +{pt}pt  ({ts})")

if __name__ == "__main__":
    main()
