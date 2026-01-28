import html
import sqlite3
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

DB_PATH = "db/holidays.sqlite"
app = FastAPI()

def db_fetchall(sql: str, params=()):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    con.close()
    return rows


def db_fetchone(sql: str, params=()):
    rows = db_fetchall(sql, params)
    return rows[0] if rows else None


def esc(s: str) -> str:
    return html.escape(s or "")


def short(s: str, n: int = 260) -> str:
    s = (s or "").strip()
    if len(s) <= n:
        return s
    return s[:n].rsplit(" ", 1)[0] + "…"


def month_from_iso(date_str: str):
    try:
        return int((date_str or "").split("-")[1])
    except Exception:
        return None


def season_by_month(m):
    if not m:
        return "neutral"
    if m in (12, 1, 2):
        return "winter"
    if m in (3, 4, 5):
        return "spring"
    if m in (6, 7, 8):
        return "summer"
    return "autumn"


def page(title: str, body: str, season: str = "neutral") -> str:
    
    return f"""
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <style>
    :root {{
      --bg1: #0b1020;
      --bg2: #161a2b;
      --card: rgba(255,255,255,0.08);
      --card2: rgba(255,255,255,0.10);
      --text: rgba(255,255,255,0.92);
      --muted: rgba(255,255,255,0.70);
      --border: rgba(255,255,255,0.12);
      --shadow: 0 20px 60px rgba(0,0,0,0.35);
      --accent: #7c5cff;
      --accent2: #2dd4bf;
      --ok: #22c55e;
      --warn: #fbbf24;
    }}

    body {{
      margin: 0;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI",
                   Roboto, "Helvetica Neue", Arial, "Noto Sans", "Apple Color Emoji",
                   "Segoe UI Emoji", "Segoe UI Symbol";
      color: var(--text);
      background:
        radial-gradient(1200px 800px at 20% 10%, rgba(124,92,255,0.35), transparent 60%),
        radial-gradient(900px 700px at 80% 30%, rgba(45,212,191,0.25), transparent 60%),
        linear-gradient(180deg, var(--bg1), var(--bg2));
      min-height: 100vh;
      overflow-x: hidden;
    }}

    /* seasonal tint */
    body[data-season="winter"] {{
      background:
        radial-gradient(1200px 800px at 20% 10%, rgba(99, 179, 237, 0.30), transparent 60%),
        radial-gradient(900px 700px at 80% 30%, rgba(255,255,255,0.10), transparent 60%),
        linear-gradient(180deg, #0b132b, #0b1020);
    }}
    body[data-season="spring"] {{
      background:
        radial-gradient(1200px 800px at 20% 10%, rgba(244,114,182,0.25), transparent 60%),
        radial-gradient(900px 700px at 80% 30%, rgba(34,197,94,0.18), transparent 60%),
        linear-gradient(180deg, #0b1020, #121a26);
    }}
    body[data-season="summer"] {{
      background:
        radial-gradient(1200px 800px at 20% 10%, rgba(250,204,21,0.22), transparent 60%),
        radial-gradient(900px 700px at 80% 30%, rgba(59,130,246,0.22), transparent 60%),
        linear-gradient(180deg, #081226, #0b1020);
    }}
    body[data-season="autumn"] {{
      background:
        radial-gradient(1200px 800px at 20% 10%, rgba(249,115,22,0.22), transparent 60%),
        radial-gradient(900px 700px at 80% 30%, rgba(245,158,11,0.18), transparent 60%),
        linear-gradient(180deg, #0b1020, #151725);
    }}

    a {{ color: inherit; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}

    .wrap {{
      max-width: 980px;
      margin: 0 auto;
      padding: 26px 18px 70px;
    }}

    .topbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      margin-bottom: 18px;
    }}

    .nav a {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 12px;
      border: 1px solid var(--border);
      border-radius: 14px;
      background: rgba(255,255,255,0.05);
      backdrop-filter: blur(8px);
    }}
    .nav a:hover {{
      background: rgba(255,255,255,0.08);
      text-decoration: none;
    }}

    .hero {{
      border: 1px solid var(--border);
      border-radius: 22px;
      background: linear-gradient(180deg, rgba(255,255,255,0.10), rgba(255,255,255,0.06));
      box-shadow: var(--shadow);
      padding: 18px;
      overflow: hidden;
      position: relative;
      flex: 1;
      text-align: center; 
    }}

    .hero::before {{
      content: "";
      position: absolute;
      inset: -120px -80px auto auto;
      width: 380px;
      height: 380px;
      background: radial-gradient(circle at 30% 30%, rgba(124,92,255,0.35), transparent 65%);
      transform: rotate(15deg);
      pointer-events: none;
    }}

    .title h1 {{
      font-size: 28px;
      margin: 0;
      letter-spacing: 0.2px;
      font-weight: 800;
    }}
    .title p {{
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 14px;
    }}

    .grid {{
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 14px;
    }}
    @media (max-width: 840px) {{
      .grid {{ grid-template-columns: 1fr; }}
    }}

    .card {{
      border: 1px solid var(--border);
      border-radius: 20px;
      background: var(--card);
      padding: 16px;
      backdrop-filter: blur(10px);
    }}

    .card h2 {{
      margin: 0 0 10px;
      font-size: 16px;
    }}
    .muted {{ color: var(--muted); }}

    input, button {{
      font: inherit;
    }}

    .row {{
      display: flex;
      gap: 10px;
    }}

    .field {{
      flex: 1;
      padding: 12px 12px;
      border-radius: 14px;
      border: 1px solid var(--border);
      background: rgba(0,0,0,0.16);
      color: var(--text);
      outline: none;
    }}
    .field::placeholder {{ color: rgba(255,255,255,0.45); }}

    .btn {{
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid rgba(124,92,255,0.40);
      background: linear-gradient(135deg, rgba(124,92,255,0.90), rgba(45,212,191,0.70));
      color: #0b1020;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 14px 40px rgba(124,92,255,0.18);
    }}
    .btn:hover {{
      filter: brightness(1.03);
    }}

    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.05);
      border-radius: 999px;
      padding: 8px 12px;
      font-size: 13px;
      color: var(--muted);
    }}

    .list {{
      margin: 0;
      padding: 0;
      list-style: none;
      display: grid;
      gap: 10px;
    }}

    .item {{
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.06);
      border-radius: 18px;
      padding: 12px 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }}

    .item a {{
      font-weight: 650;
    }}

    .tag {{
      font-size: 12px;
      padding: 6px 10px;
      border-radius: 999px;
      border: 1px solid var(--border);
      color: var(--muted);
      background: rgba(0,0,0,0.12);
      white-space: nowrap;
    }}

    .tag.ok {{
      border-color: rgba(34,197,94,0.35);
      color: rgba(34,197,94,0.95);
      background: rgba(34,197,94,0.10);
      font-weight: 700;
    }}

    .descbox {{
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.07);
      border-radius: 20px;
      padding: 14px;
      margin: 14px 0;
    }}
    .descbox .src {{
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 6px;
    }}
    .descbox .txt {{
      font-size: 15px;
      line-height: 1.45;
      color: rgba(255,255,255,0.92);
    }}

    /* particles layer */
    .particles {{
      position: fixed;
      inset: 0;
      pointer-events: none;
      overflow: hidden;
      z-index: 0;
    }}
    .wrap, .hero {{ position: relative; z-index: 1; }}

    .p {{
      position: absolute;
      top: -40px;
      opacity: 0.85;
      animation: fall linear infinite;
      filter: drop-shadow(0 8px 16px rgba(0,0,0,0.25));
      user-select: none;
    }}
    @keyframes fall {{
      to {{
        transform: translateY(110vh) translateX(var(--drift));
      }}
    }}
  </style>
</head>
<body data-season="{esc(season)}">
  <div class="particles" id="particles"></div>

  <div class="wrap">
    <div class="topbar">
      <div class="hero">
        <div class="title">
          <h1>Какой сегодня праздник?</h1>
          <p>Поиск и просмотр праздников по датам</p>
        </div>
      </div>
      <div class="nav">
        <a href="/">🏠 Главная</a>
      </div>
    </div>

    {body}
  </div>

<script>
(function() {{
  const season = document.body.getAttribute("data-season") || "neutral";
  const layer = document.getElementById("particles");
  if (!layer) return;

  let glyphs = ["•"];
  let count = 0;

  if (season === "winter") {{ glyphs = ["❄","❅","✻"]; count = 26; }}
  else if (season === "spring") {{ glyphs = ["🌸","💮","🌼"]; count = 20; }}
  else if (season === "summer") {{ glyphs = ["✨","⭐","🌟"]; count = 18; }}
  else if (season === "autumn") {{ glyphs = ["🍂","🍁","🍃"]; count = 20; }}
  else {{ glyphs = ["•"]; count = 0; }}

  function rnd(a,b) {{ return a + Math.random()*(b-a); }}

  for (let i=0; i<count; i++) {{
    const el = document.createElement("div");
    el.className = "p";
    el.textContent = glyphs[Math.floor(Math.random()*glyphs.length)];
    el.style.left = rnd(0, 100) + "vw";
    el.style.fontSize = rnd(12, 26) + "px";
    el.style.animationDuration = rnd(8, 18) + "s";
    el.style.animationDelay = rnd(0, 6) + "s";
    el.style.setProperty("--drift", (rnd(-12, 12)) + "vw");
    el.style.opacity = rnd(0.45, 0.9);
    layer.appendChild(el);
  }}
}})();
</script>

</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def home():
    body = """
    <div class="hero">
      <div class="grid">
        <div class="card">
          <h2>Поиск по названию</h2>
          <form action="/search" method="get" class="row">
            <input class="field" name="q" placeholder="Например: Новый год, Барби, ананаса...">
            <button class="btn" type="submit">Найти</button>
          </form>
          <div style="height:10px;"></div>
          <div class="pill">Совет: ищи по ключевым словам (например “день”, “международный”, “world”).</div>
        </div>

        <div class="card">
          <h2>Открыть дату</h2>
          <form action="/date" method="get" class="row">
            <input class="field" name="d" placeholder="YYYY-MM-DD (например 2025-03-09)">
            <button class="btn" type="submit">Открыть</button>
          </form>
          <div style="height:10px;"></div>
          <div class="pill">📝 означает: есть описание (обычно из my-calend.ru)</div>
        </div>
      </div>

      <div style="height:14px;"></div>

      <div class="card">
        <h2>Быстрые примеры</h2>
       <div class="row" style="flex-wrap:wrap; justify-content:center; gap:12px;">
          <a class="pill" href="/date?d=2025-01-01">🎄 2025-01-01</a>
          <a class="pill" href="/date?d=2025-03-09">🌸 2025-03-09</a>
          <a class="pill" href="/date?d=2025-11-19">🍂 2025-11-19</a>
          <a class="pill" href="/search?q=%D0%9D%D0%BE%D0%B2%D1%8B%D0%B9%20%D0%B3%D0%BE%D0%B4">🔎 Новый год</a>
        </div>
      </div>
    </div>
    """
    return page("Поиск праздника — Главная", body, season="neutral")


@app.get("/date", response_class=HTMLResponse)
def by_date(d: str = Query(..., description="YYYY-MM-DD")):
    rows = db_fetchall("""
    SELECT
        o.id AS occ_id,
        h.canonical_title,
        h.lang,
        MAX(CASE WHEN trim(coalesce(m.description,'')) != '' THEN 1 ELSE 0 END) AS has_desc
    FROM occurrences o
    JOIN holidays h ON h.id = o.holiday_id
    JOIN mentions m ON m.occurrence_id = o.id
    WHERE o.date = ?
    GROUP BY o.id, h.canonical_title, h.lang
    ORDER BY
        CASE WHEN h.lang='ru' THEN 0 ELSE 1 END,
        has_desc DESC,
        h.canonical_title
    LIMIT 700
    """, (d,))

    season = season_by_month(month_from_iso(d))

    if not rows:
        body = f"""
        <div class="hero">
          <div class="card">
            <h2>На дату {esc(d)} ничего не найдено</h2>
            <div class="muted">Попробуй другую дату (формат YYYY-MM-DD)</div>
          </div>
        </div>
        """
        return page(f"Праздники на {d}", body, season=season)

    items = []
    for r in rows:
        icon = "<span class='tag ok'>📝 есть описание</span>" if r["has_desc"] else "<span class='tag'>без описания</span>"
        items.append(
            f"""
            <li class="item">
              <div>
                <a href="/occurrence/{r['occ_id']}">{esc(r['canonical_title'])}</a>
                <span class="muted" style="margin-left:8px; font-size:12px;">({esc(r['lang'])})</span>
              </div>
              {icon}
            </li>
            """
        )

    body = f"""
    <div class="hero">
      <div class="card">
        <h2>Праздники на дату <span style="color: rgba(255,255,255,0.95)">{esc(d)}</span></h2>
        <div class="muted">Сначала русские, затем английские. Сверху — те, где есть описание 📝</div>
      </div>

      <div style="height:12px;"></div>

      <ul class="list">
        {''.join(items)}
      </ul>
    </div>
    """
    return page(f"Праздники на {d}", body, season=season)


@app.get("/occurrence/{occ_id}", response_class=HTMLResponse)
def occurrence(occ_id: int):
    info = db_fetchone("""
      SELECT o.date, h.canonical_title, h.lang
      FROM occurrences o
      JOIN holidays h ON h.id = o.holiday_id
      WHERE o.id = ?
    """, (occ_id,))
    if not info:
        body = "<div class='hero'><div class='card'><h2>Не найдено</h2></div></div>"
        return page("Не найдено", body)

    mentions = db_fetchall("""
      SELECT s.name AS source, m.title_raw, m.description, m.url
      FROM mentions m
      JOIN sources s ON s.id = m.source_id
      WHERE m.occurrence_id = ?
      ORDER BY
        CASE s.name
            WHEN 'my-calend.ru' THEN 0
            WHEN 'calend.ru' THEN 1
            WHEN 'wikipedia.org' THEN 2
            ELSE 9
        END
    """, (occ_id,))

    best = None
    for src in ("my-calend.ru", "calend.ru", "wikipedia.org"):
        for m in mentions:
            if m["source"] == src and (m["description"] or "").strip():
                best = m
                break
        if best:
            break

    if best:
        best_box = f"""
        <div class="descbox">
          <div class="src">Описание (источник: <b>{esc(best['source'])}</b>)</div>
          <div class="txt">{esc(best['description'])}</div>
        </div>
        """
    else:
        best_box = """
        <div class="descbox">
          <div class="src">Описание</div>
          <div class="txt muted">Описание для этого праздника пока не найдено.</div>
        </div>
        """

    m_items = []
    for m in mentions:
        same_as_best = bool(best and m["source"] == best["source"] and (m["description"] or "").strip())

        desc_html = ""
        if not same_as_best:
            desc = short(m["description"] or "", 260)
            if desc:
                desc_html = f"<div class='muted' style='margin-top:6px; line-height:1.35;'>{esc(desc)}</div>"

        m_items.append(
            f"""
            <li class="item" style="align-items:flex-start;">
              <div style="flex:1;">
                <div class="muted" style="font-size:12px;">{esc(m['source'])}</div>
                <div style="margin-top:4px;">
                  <a href="{esc(m['url'])}" target="_blank">{esc(m['title_raw'])}</a>
                </div>
                {desc_html}
              </div>
              <span class="tag">{'📝' if (m['description'] or '').strip() else '—'}</span>
            </li>
            """
        )

    body = f"""
    <div class="hero">
      <div class="card">
        <h2>{esc(info['canonical_title'])} <span class="muted">({esc(info['lang'])})</span></h2>
        <div class="muted">
          Дата: <a href="/date?d={esc(info['date'])}" style="text-decoration: underline;">{esc(info['date'])}</a>
        </div>
      </div>

      {best_box}

      <div class="card">
        <h2>Упоминания в источниках</h2>
        <ul class="list">{''.join(m_items)}</ul>
      </div>

      <div style="height:12px;"></div>
      <div class="card">
        <a class="pill" href="/date?d={esc(info['date'])}">← Назад к дате</a>
        <a class="pill" href="/" style="margin-left:10px;">🏠 На главную</a>
      </div>
    </div>
    """

    season = season_by_month(month_from_iso(info["date"]))
    return page(info["canonical_title"], body, season=season)


@app.get("/search", response_class=HTMLResponse)
def search(q: str = Query(...)):
    q = (q or "").strip()
    if not q:
        body = "<div class='hero'><div class='card'><h2>Пустой запрос</h2></div></div>"
        return page("Поиск", body)

    like = f"%{q}%"
    rows = db_fetchall("""
      SELECT h.id, h.canonical_title, h.lang
      FROM holidays h
      WHERE h.canonical_title LIKE ?
      ORDER BY CASE WHEN h.lang='ru' THEN 0 ELSE 1 END, h.canonical_title
      LIMIT 200
    """, (like,))

    if not rows:
        body = f"""
        <div class="hero">
          <div class="card">
            <h2>Ничего не найдено</h2>
            <div class="muted">Запрос: {esc(q)}</div>
          </div>
        </div>
        """
        return page("Поиск", body)

    items = []
    for r in rows:
        items.append(
            f"""
            <li class="item">
              <div>
                <div style="font-weight:650;">{esc(r['canonical_title'])}</div>
                <div class="muted" style="font-size:12px;">язык: {esc(r['lang'])}</div>
              </div>
              <span class="tag">найдено</span>
            </li>
            """
        )

    body = f"""
    <div class="hero">
      <div class="card">
        <h2>Результаты поиска</h2>
        <div class="muted">Запрос: <b>{esc(q)}</b> • найдено: {len(rows)}</div>
      </div>

      <div style="height:12px;"></div>

      <ul class="list">{''.join(items)}</ul>
    </div>
    """
    return page("Поиск", body)
