import json
from pathlib import Path
from datetime import datetime, date
from zoneinfo import ZoneInfo

BASE = Path(__file__).parent
DATA = BASE / "points.json"
SITE = BASE / "docs"
JST = ZoneInfo("Asia/Tokyo")

def load_log():
    if not DATA.exists():
        return []
    data = json.loads(DATA.read_text(encoding="utf-8"))
    return data.get("log", [])

def parse_ts(ts: str) -> datetime:
    # ts例: 2026-01-01T21:10:00+09:00
    return datetime.fromisoformat(ts)

def sum_by_name(events):
    totals = {}
    for e in events:
        name = str(e.get("name", "")).strip()
        pt = int(e.get("pt", 0))
        if not name or pt <= 0:
            continue
        totals[name] = totals.get(name, 0) + pt
    return totals

def filter_daily(log, today: date):
    out = []
    for e in log:
        try:
            dt = parse_ts(e["ts"]).astimezone(JST)
        except Exception:
            continue
        if dt.date() == today:
            out.append(e)
    return out

def filter_monthly(log, year: int, month: int):
    out = []
    for e in log:
        try:
            dt = parse_ts(e["ts"]).astimezone(JST)
        except Exception:
            continue
        if dt.year == year and dt.month == month:
            out.append(e)
    return out

def chart_page(title, totals, active):
    # 並びはpt降順
    ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    labels = [n for n, _ in ranked]
    values = [v for _, v in ranked]

    # タブ（スプレッドシートっぽく）
    def tab(text, href, key):
        cls = "tab active" if key == active else "tab"
        return f'<a class="{cls}" href="{href}">{text}</a>'

    tabs = (
        tab("日間", "daily.html", "daily") +
        tab("月間", "monthly.html", "monthly") +
        tab("累計", "total.html", "total")
    )

    # 上位表示テーブル（任意）
    rows = "\n".join(
        f"<tr><td>{i}</td><td>{name}</td><td>{pt}</td></tr>"
        for i, (name, pt) in enumerate(ranked[:20], start=1)
    ) or "<tr><td colspan='3'>(データなし)</td></tr>"

    updated = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body {{
  margin: 0; padding: 16px;
  background: #0f0f0f; color: #fff;
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
}}
.container {{ max-width: 900px; margin: 0 auto; }}
h1 {{ font-size: 22px; margin: 8px 0 12px; }}
.muted {{ color: #aaa; font-size: 12px; margin-bottom: 12px; }}
.tabs {{ display: flex; gap: 8px; margin: 8px 0 16px; }}
.tab {{
  text-decoration: none; color: #ddd;
  border: 1px solid #333; padding: 8px 12px;
  border-radius: 10px; background: #151515;
}}
.tab.active {{
  border-color: #777; color: #fff;
  background: #1d1d1d;
}}
.card {{
  border: 1px solid #222; background: #121212;
  border-radius: 14px; padding: 14px;
  margin-bottom: 14px;
}}
table {{ width: 100%; border-collapse: collapse; }}
td, th {{ border-bottom: 1px solid #222; padding: 8px; text-align: left; }}
th {{ color: #bbb; font-weight: 600; }}
</style>
</head>
<body>
  <div class="container">
    <h1>{title}</h1>
    <div class="muted">更新: {updated}（JST）</div>

    <div class="tabs">{tabs}</div>

    <div class="card">
      <canvas id="chart"></canvas>
    </div>

    <div class="card">
      <h2 style="font-size:16px;margin:0 0 8px;">ランキング（上位20）</h2>
      <table>
        <thead><tr><th>#</th><th>名前</th><th>pt</th></tr></thead>
        <tbody>
          {rows}
        </tbody>
      </table>
    </div>
  </div>

<script>
const labels = {labels};
const data = {values};

new Chart(document.getElementById("chart"), {{
  type: "bar",
  data: {{
    labels,
    datasets: [{{ data }}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ display: false }}
    }},
    scales: {{
      x: {{
        ticks: {{ color: "#ddd" }},
        grid: {{ color: "#222" }}
      }},
      y: {{
        ticks: {{ color: "#ddd" }},
        grid: {{ color: "#222" }}
      }}
    }}
  }}
}});
</script>

</body>
</html>
"""

def write_file(name, content):
    SITE.mkdir(exist_ok=True)
    (SITE / name).write_text(content, encoding="utf-8")

def main():
    log = load_log()

    now = datetime.now(JST)
    today = now.date()

    daily_events = filter_daily(log, today)
    monthly_events = filter_monthly(log, now.year, now.month)

    daily_totals = sum_by_name(daily_events)
    monthly_totals = sum_by_name(monthly_events)
    total_totals = sum_by_name(log)

    write_file("daily.html",   chart_page("📊 応援pt（日間）", daily_totals, "daily"))
    write_file("monthly.html", chart_page("📊 応援pt（月間）", monthly_totals, "monthly"))
    write_file("total.html",   chart_page("📊 応援pt（累計）", total_totals, "total"))

    # indexは月間に飛ばす（好みでdailyにしてもOK）
    index = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8" />
<meta http-equiv="refresh" content="0; url=monthly.html" />
<title>応援pt集計</title>
</head>
<body>
<a href="monthly.html">移動</a>
</body>
</html>
"""
    write_file("index.html", index)

    print("OK: docs/ に daily.html, monthly.html, total.html, index.html を生成しました")

if __name__ == "__main__":
    main()
