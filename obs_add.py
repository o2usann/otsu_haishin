import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

BASE = Path(__file__).parent
DATA = BASE / "points.json"
JST = timezone(timedelta(hours=9))

def load():
    if DATA.exists():
        return json.loads(DATA.read_text(encoding="utf-8"))
    return {"log": []}

def save(data):
    DATA.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def main():
    if len(sys.argv) != 3:
        print("usage: obs_add.py <name> <pt>")
        return

    name = sys.argv[1]
    pt = int(sys.argv[2])

    data = load()
    ts = datetime.now(JST).isoformat(timespec="seconds")

    data["log"].append({
        "ts": ts,
        "name": name,
        "pt": pt
    })

    save(data)
    print(f"OK: {name} +{pt}")

if __name__ == "__main__":
    main()
