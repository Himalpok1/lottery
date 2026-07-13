#!/usr/bin/env python3
"""
Pulls the draw-game results off the texaslottery.com homepage.

The homepage carries a card for each of the eight draw games — Powerball, Mega Millions,
Lotto Texas, Texas Two Step, Pick 3, Daily 4, Cash Five, All or Nothing — with the current
jackpot, the next draw date, and the latest winning numbers. This module reads that one
page and turns it into plain data for the TV board's results strip.

Same story as tx_fetch.py: the browser can't read texaslottery.com itself (no CORS
headers), so server.py calls fetch_draws() and hands the result to the app.

Run on its own:   python3 tx_draws_fetch.py
"""
import json
import re
import urllib.request

HOME_URL = "https://www.texaslottery.com/"
UA = "Mozilla/5.0 (compatible; LotteryDisplay/1.0; store signage)"

# Every game card on the homepage is an <a class="black"> around a homePageCell
CELL_RE = re.compile(
    r'<a class="black" href="/export/sites/lottery/Games/([A-Za-z_0-9]+)/index\.html">(.*?)</a>',
    re.S,
)
LOGO_RE = re.compile(r'<img[^>]*src="([^"]+)"', re.I)
# "<p>Est. Annuitized Jackpot</p> <h1>$478 Million</h1>" — the label and the money
HEAD_RE = re.compile(r"<p>([^<]*(?:Jackpot|Top Prize)[^<]*)</p>\s*<h1>([^<]+)</h1>", re.S)
CASH_RE = re.compile(r"Est\. Cash Value:\s*<strong>([^<]+)</strong>")
NEXT_RE = re.compile(r"Next Draw:\s*<strong>([^<]+)</strong>")
# "Results for: <strong>07/11/2026</strong>"  or, for the four-a-day games,
# "Results for <strong>Morning</strong> Draw: <strong>07/13/2026</strong>"
RESULT_RE = re.compile(
    r"Results for\s*(?:<strong>(\w+)</strong>\s*Draw)?:?\s*<strong>([\d/]+)</strong>\s*</p>"
    r'\s*<ol class="winningNumberBalls"[^>]*>(.*?)</ol>',
    re.S,
)
BALL_RE = re.compile(r'<li><span(?:\s+class="([^"]*)")?\s*>(\d+)</span></li>')
MULT_RE = re.compile(r"Power Play X\s*<strong>(\d+)</strong>")

NAMES = {
    "Powerball": "Powerball",
    "Mega_Millions": "Mega Millions",
    "Lotto_Texas": "Lotto Texas",
    "Texas_Two_Step": "Texas Two Step",
    "Pick_3": "Pick 3",
    "Daily_4": "Daily 4",
    "Cash_Five": "Cash Five",
    "All_or_Nothing": "All or Nothing",
}
ORDER = list(NAMES)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def fetch_draws():
    """Returns ([game, ...], note). Each game is a plain dict the board can render."""
    html = get(HOME_URL)
    # The live cards sit inside GamesGrid; the same markup also appears commented-out
    # higher up the page, so only read from the grid down.
    cut = html.find('id="GamesGrid"')
    if cut != -1:
        html = html[cut:]

    seen = {}
    for key, body in CELL_RE.findall(html):
        if key not in NAMES or key in seen:
            continue
        g = {"key": key, "name": NAMES[key]}
        m = LOGO_RE.search(body)
        if m:
            src = m.group(1)
            g["logo"] = src if src.startswith("http") else "https://www.texaslottery.com" + src
        m = HEAD_RE.search(body)
        if m:
            g["label"] = re.sub(r"\s+", " ", m.group(1)).strip()
            g["amount"] = m.group(2).strip()
        g["alert"] = "JACKPOT ALERT" in body
        m = CASH_RE.search(body)
        if m:
            g["cash"] = m.group(1).strip()
        m = NEXT_RE.search(body)
        if m:
            g["next"] = re.sub(r"\s+", " ", m.group(1)).strip()
        m = MULT_RE.search(body)
        if m:
            g["mult"] = "Power Play X " + m.group(1)
        g["results"] = [
            {
                "label": (label or "").strip(),
                "date": date,
                "nums": [{"n": n, "cls": cls or ""} for cls, n in BALL_RE.findall(balls)],
            }
            for label, date, balls in RESULT_RE.findall(body)
        ]
        seen[key] = g

    games = [seen[k] for k in ORDER if k in seen]
    if not games:
        raise RuntimeError("no draw games found — texaslottery.com may have changed its homepage")
    return games, f"{len(games)} draw games"


if __name__ == "__main__":
    games, note = fetch_draws()
    with open("tx-draws.json", "w") as f:
        json.dump(games, f, indent=1)
    print(f"wrote tx-draws.json — {note}")
    for g in games:
        latest = g["results"][0] if g["results"] else None
        nums = " ".join(b["n"] for b in latest["nums"]) if latest else "—"
        print(f"  {g['name']:<16} {g.get('amount','—'):<14} {nums}")
