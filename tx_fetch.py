#!/usr/bin/env python3
"""
Pulls the live scratch-off catalog straight from texaslottery.com.

The browser can't do this itself — texaslottery.com doesn't send CORS headers, so a web
page on another origin is blocked from reading it. Python has no such restriction, so the
server does the fetching and hands the result to the app.

Two pages are read:

  Games by Price Point  -> every current game: number, name, price, start date, ticket art
  https://www.texaslottery.com/export/sites/lottery/Games/Scratch_Offs/index.html

  Games Ending Soon     -> which games the state has called, and which have zero top prizes
  https://www.texaslottery.com/export/sites/lottery/Games/Scratch_Offs/closing.html

Run on its own:   python3 tx_fetch.py
Writes tx-scratchoffs.json. The server calls fetch_all() for the "Fetch live" button.
"""
import json
import re
import urllib.request
from html import unescape

BASE = "https://www.texaslottery.com/export/sites/lottery/Games/Scratch_Offs/"
PRICE_POINT_URL = BASE + "index.html"
CLOSING_URL = BASE + "closing.html"
UA = "Mozilla/5.0 (compatible; LotteryDisplay/1.0; store signage)"

# The ticket art filename carries the game number: .../scratchoffs/2747_200X200.gif
IMG_RE = re.compile(r"scratchoffs/(\d{3,5})_200X200\.(?:gif|png|jpg)", re.I)
IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.I)
SRC_ATTR_RE = re.compile(r'src\s*=\s*"([^"]+)"', re.I)
ALT_ATTR_RE = re.compile(r'alt\s*=\s*"([^"]*)"', re.I)
PRICE_RE = re.compile(r"Ticket\s*Price:\s*\$?\s*([\d,]+)", re.I)
START_RE = re.compile(r"Start:\s*(\d{2}/\d{2}/\d{4})", re.I)
# On the closing page each row links out with this title
CLOSE_NUM_RE = re.compile(r'title="View Ticket Details for Game Number (\d+)"', re.I)
DATE_RE = re.compile(r"(\d{2}/\d{2}/\d{4})")

TAGS = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def _text(s):
    """Strip tags so 'Ticket Price: $5' survives whatever markup wraps it."""
    return WS.sub(" ", TAGS.sub(" ", s))


def parse_price_point(html):
    """One record per ticket image on the page."""
    games = {}
    for tag in IMG_TAG_RE.finditer(html):
        # Read src and alt from THIS <img> tag — never from a neighbouring card.
        src = SRC_ATTR_RE.search(tag.group(0))
        if not src:
            continue
        num = IMG_RE.search(src.group(1))
        if not num:
            continue  # a banner or logo, not a ticket
        no = num.group(1)

        alt_attr = ALT_ATTR_RE.search(tag.group(0))
        alt = unescape(alt_attr.group(1)) if alt_attr else ""
        kind = "feature" if re.search(r"View Feature", alt, re.I) else "ticket"
        name = re.sub(r"^View (?:Ticket|Feature|Featured Game) Details for\s*", "", alt, flags=re.I)
        name = WS.sub(" ", name).strip()

        # Price and start date sit just after the card's image.
        fwd = _text(html[tag.end(): tag.end() + 700])
        pm = PRICE_RE.search(fwd)
        sm = START_RE.search(fwd)
        price = int(pm.group(1).replace(",", "")) if pm else None
        start = sm.group(1) if sm else None

        g = games.get(no)
        if g is None:
            g = {
                "no": no, "name": name, "price": price, "start": start,
                "img": f"https://www.texaslottery.com/export/sites/lottery/Images/scratchoffs/{no}_200X200.gif",
                "details": None, "featured": False, "new": False,
                "closing": False, "endDate": None, "prizesLeft": None,
            }
            games[no] = g

        # A game appears twice: once in the Featured strip, once in its price section.
        # The Featured card carries no price, so only trust price/start from a priced card —
        # otherwise a featured game picks up the next section's date.
        if kind == "feature":
            g["featured"] = True
        if name:
            # The game's own ticket card is authoritative; the Featured strip only fills gaps.
            if kind == "ticket" or not g["name"]:
                g["name"] = name
        if price is not None:
            if g["price"] is None:
                g["price"] = price
            if start and not g["start"]:
                g["start"] = start

    # "New Tickets" is its own section — anything listed there is new.
    nm = re.search(r"New Tickets(.*?)(?:\$1 Scratch|\Z)", html, re.S | re.I)
    if nm:
        for m in IMG_RE.finditer(nm.group(1)):
            if m.group(1) in games:
                games[m.group(1)]["new"] = True

    # Drop anything with no price at all — those are banners, not tickets.
    return {k: v for k, v in games.items() if v["price"]}


def parse_closing(html):
    """
    Three sections matter:
      Pre-Call Announcements                    -> called soon, prizes unknown
      Games Closing with Top Prize Unclaimed    -> called, prizes still out there
      Games Closing with Zero Top Prizes        -> called, prizesLeft = 0
    """
    out = {}
    zero_at = re.search(r"Zero Top Prizes", html, re.I)
    zero_pos = zero_at.start() if zero_at else len(html) + 1

    for m in CLOSE_NUM_RE.finditer(html):
        no = m.group(1)
        row = _text(html[m.end(): m.end() + 400])
        dates = DATE_RE.findall(row)
        # columns run: Game Call Date, End of Game Date, [Last Day to Redeem]
        end_date = dates[1] if len(dates) > 1 else (dates[0] if dates else None)
        out[no] = {
            "closing": True,
            "endDate": end_date,
            "prizesLeft": 0 if m.start() > zero_pos else None,
        }
    return out


def fetch_all():
    """Returns (games_list, note). Raises on network failure."""
    games = parse_price_point(get(PRICE_POINT_URL))
    if len(games) < 15:
        raise ValueError(
            f"only parsed {len(games)} games — the Texas Lottery page layout probably changed"
        )
    note = f"{len(games)} games"

    # The closing page is a bonus; if it moves, don't lose the whole catalog over it.
    try:
        closing = parse_closing(get(CLOSING_URL))
        hit = 0
        for no, c in closing.items():
            if no in games:
                games[no].update(c)
                hit += 1
        note += f", {hit} closing"
    except Exception as e:
        note += f" (closing page unavailable: {e})"

    ordered = sorted(games.values(), key=lambda g: (g["price"], g["no"]))
    return ordered, note


if __name__ == "__main__":
    try:
        games, note = fetch_all()
    except Exception as e:
        raise SystemExit(f"Could not fetch: {e}")

    with open("tx-scratchoffs.json", "w") as f:
        json.dump(games, f, indent=1)

    print(f"wrote tx-scratchoffs.json — {note}")
    by = {}
    for g in games:
        by[g["price"]] = by.get(g["price"], 0) + 1
    for p in sorted(by):
        print(f"  ${p:<4} {by[p]:>2} games")
    for g in games:
        if g["closing"]:
            tag = "0 top prizes left" if g["prizesLeft"] == 0 else "prizes unclaimed"
            print(f"    CLOSING #{g['no']} {g['name'][:28]:<30} ends {g['endDate']} ({tag})")
