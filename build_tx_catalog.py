#!/usr/bin/env python3
"""
Builds tx-scratchoffs.json from the Texas Lottery "Games by Price Point" page.

Data captured 2026-07-13 from:
https://www.texaslottery.com/export/sites/lottery/Games/Scratch_Offs/index.html

Each record: game number, name, price, start date, ticket image, details page.
Ticket art is hotlinked from texaslottery.com (no download, no storage cost).

Re-run this whenever the state adds or ends games.
"""
import json

IMG = "https://www.texaslottery.com/export/sites/lottery/Images/scratchoffs/{}_200X200.gif"
DET = "https://www.texaslottery.com/export/sites/lottery/Games/Scratch_Offs/details.html_{}.html"

# (game_no, name, price, start, details_id)
GAMES = [
    # --- New tickets ---
    ("2747", "Ms. PAC-MAN",                     5,  "07/20/2026", "252698645"),
    ("2753", "$1,000,000 Crossword",           20,  "07/20/2026", "252698618"),
    # --- $1 ---
    ("2710", "9s In A Line",                    1,  "01/20/2026", "252698745"),
    # --- $2 ---
    ("2739", "King of Cash",                    2,  "06/15/2026", "252698674"),
    ("2715", "Find $200",                       2,  "05/18/2026", "252698740"),
    ("2646", "20X The Money",                   2,  "03/02/2026", "252699607"),
    ("2672", "Royal Riches",                    2,  "01/20/2026", "252699518"),
    ("2622", "Lucky No. 7",                     2,  "12/15/2025", "252699673"),
    ("2656", "Crazy 8s",                        2,  "11/17/2025", "252699576"),
    ("2692", "Patriotic Payout",                2,  "10/20/2025", "252699456"),
    ("2686", "$30,000 Gold Rush",               2,  "09/15/2025", "252699483"),
    ("2700", "Break the Bank",                  2,  "08/04/2025", "252698776"),
    ("2647", "Cash Line Bingo",                 2,  "07/21/2025", "252699606"),
    # --- $3 ---
    ("2662", "Cashword",                        3,  "04/13/2026", "252699549"),
    ("2711", "30X The Cash Word Search",        3,  "01/05/2026", "252698744"),
    ("2628", "Texas Loteria",                   3,  "05/19/2025", "252699667"),
    ("2504", "Crossword",                       3,  "03/04/2024", "252700694"),
    # --- $5 ---
    ("2743", "Super Loteria",                   5,  "07/01/2026", "252698649"),
    ("2745", "Airstream Dream",                 5,  "06/15/2026", "252698647"),
    ("2740", "Super Crossword",                 5,  "06/03/2026", "252698652"),
    ("2727", "All About the 8s",                5,  "06/01/2026", "252698707"),
    ("2765", "Loteria Azul",                    5,  "05/18/2026", "252698585"),
    ("2736", "Monaco Cash",                     5,  "04/27/2026", "252698677"),
    ("2577", "$100,000 Cash",                   5,  "04/13/2026", "252700474"),
    ("2728", "Yellowstone",                     5,  "03/30/2026", "252698706"),
    ("2723", "Lucky 7s Tripler",                5,  "03/16/2026", "252698711"),
    ("2660", "In the Green",                    5,  "03/02/2026", "252699551"),
    ("2720", "Chameleon Cash",                  5,  "02/16/2026", "252698714"),
    ("2751", "Azulejos",                        5,  "02/02/2026", "252698620"),
    ("2712", "50X The Cash",                    5,  "01/05/2026", "252698743"),
    ("2667", "Bingo Times 20",                  5,  "12/01/2025", "252699544"),
    ("2683", "Emerald 7s",                      5,  "09/02/2025", "252699486"),
    ("2430", "Bonus Break the Bank",            5,  "07/07/2025", "252701566"),
    ("2648", "Super Loteria",                   5,  "04/21/2025", "252699605"),
    # --- $10 ---
    ("2733", "Mega Cash!",                     10,  "06/15/2026", "252698680"),
    ("2737", "Monaco VIP",                     10,  "04/27/2026", "252698676"),
    ("2724", "Slots of Luck",                  10,  "03/30/2026", "252698710"),
    ("2632", "777",                            10,  "03/02/2026", "252699642"),
    ("2636", "$1,000,000 Riches",              10,  "02/02/2026", "252699638"),
    ("2713", "100X The Cash",                  10,  "01/05/2026", "252698742"),
    ("2705", "Lucky Match",                    10,  "12/01/2025", "252698771"),
    ("2699", "Reindeer Riches",                10,  "11/03/2025", "252699449"),
    ("2691", "100X Sonic Blast",               10,  "10/06/2025", "252699457"),
    ("2668", "$250,000 50X Cashword",          10,  "09/15/2025", "252699543"),
    ("2669", "Mega Loteria",                   10,  "08/04/2025", "252699542"),
    ("2637", "$50, $100 OR $500!",             10,  "07/07/2025", "252699637"),
    ("2676", "Limited Edition Mega Loteria",   10,  "06/23/2025", "252699514"),
    # --- $20 ---
    ("2613", "200X The Cash",                  20,  "07/01/2026", "252699703"),
    ("2706", "Queen of Spades",                20,  "06/01/2026", "252698770"),
    ("2738", "Monaco Millionaire",             20,  "04/27/2026", "252698675"),
    ("2725", "Power 20s",                      20,  "03/16/2026", "252698709"),
    ("2722", "Mega Millionaire",               20,  "02/16/2026", "252698712"),
    ("2714", "200X The Cash",                  20,  "01/05/2026", "252698741"),
    ("2744", "$1,000,000 Ca$h!",               20,  "12/01/2025", "252698648"),
    ("2671", "Instant Millions",               20,  "10/20/2025", "252699519"),
    ("2685", "Diamond 7s",                     20,  "09/02/2025", "252699484"),
    ("2655", "Extreme Multiplier",             20,  "08/04/2025", "252699577"),
    ("2653", "Million Dollar Loteria",         20,  "07/21/2025", "252699579"),
    ("2658", "$1,000,000 Crossword",           20,  "06/16/2025", "252699574"),
    ("2609", "$100, $200, $500 OR $1,000!",    20,  "11/18/2024", "252699728"),
    # --- $30 ---
    ("2730", "Millionaire's Club",             30,  "03/30/2026", "252698683"),
    ("2661", "Premier Play",                   30,  "08/04/2025", "252699550"),
    ("2633", "$3 Million Ca$h",                30,  "04/07/2025", "252699641"),
    # --- $50 ---
    ("2610", "Ultimate Millions",              50,  "04/13/2026", "252699706"),
    ("2689", "Casino Millions",                50,  "01/20/2026", "252699480"),
    ("2677", "Golden Riches",                  50,  "11/17/2025", "252699513"),
    ("2659", "500X Loteria Spectacular",       50,  "09/15/2025", "252699573"),
    ("2624", "$5 Million Royale",              50,  "04/21/2025", "252699671"),
    ("2590", "X",                              50,  "01/21/2025", "252700419"),
    ("2589", "500X",                           50,  "09/16/2024", "252700441"),
    # --- $100 ---
    ("2627", "$5 Million Titanium Black",     100,  "02/02/2026", "252699668"),
    ("2587", "Loteria Supreme",               100,  "08/18/2025", "252700443"),
    ("2665", "$5,000,000 Fortune",            100,  "02/03/2025", "252699546"),
    ("2400", "$20 Million Supreme",           100,  "05/16/2022", "252701659"),
]

# From the state's "Games Ending Soon" page (closing.html), captured 13 Jul 2026.
# no -> (end_of_game_date, top_prizes_left)
#   Pre-Call         = announced, still has prizes  -> prizes unknown (None)
#   Top Prize Unclaimed = closing, top prizes still out there -> None
#   Zero Top Prizes  = closing with NO top prizes left -> 0
CLOSING = {
    # --- Pre-Call Announcements ---
    "2609": ("09/02/2026", None),   # $100, $200, $500 OR $1,000!
    "2637": ("09/02/2026", None),   # $50, $100 OR $500!
    "2691": ("08/12/2026", None),   # 100X Sonic Blast
    "2692": ("08/12/2026", None),   # Patriotic Payout
    "2699": ("08/12/2026", None),   # Reindeer Riches
    # --- Called: closing with top prize tickets UNCLAIMED ---
    "2633": ("07/15/2026", None),   # $3 Million Ca$h
    "2686": ("07/15/2026", None),   # $30,000 Gold Rush
    "2504": ("07/15/2026", None),   # Crossword
    # --- Called: closing with ZERO top prizes remaining ---
    "2723": ("08/07/2026", 0),      # Lucky 7s Tripler
}

# Games the state currently flags as Featured on the price-point page.
FEATURED = {"2745", "2736", "2737", "2738", "2712", "2711", "2713", "2714", "2633"}
# Games listed under "New Tickets".
NEW = {"2747", "2753"}

out = []
for no, name, price, start, det in GAMES:
    out.append({
        "no": no,
        "name": name,
        "price": price,
        "start": start,
        "img": IMG.format(no),
        "details": DET.format(det),
        "featured": no in FEATURED,
        "new": no in NEW,
        "closing": no in CLOSING,
        "endDate": CLOSING[no][0] if no in CLOSING else None,
        # Prizes remaining is NOT on the price-point page — it lives on each game's detail
        # page. The only ones the state hands us are the "zero top prizes" closers.
        "prizesLeft": CLOSING[no][1] if no in CLOSING else None,
    })

with open("tx-scratchoffs.json", "w") as f:
    json.dump(out, f, indent=1)

by_price = {}
for g in out:
    by_price[g["price"]] = by_price.get(g["price"], 0) + 1
print(f"wrote tx-scratchoffs.json — {len(out)} games")
for p in sorted(by_price):
    print(f"  ${p:<4} {by_price[p]:>2} games")
print(f"  featured: {len(FEATURED)} · new: {len(NEW)} · closing: {sum(1 for g in out if g['closing'])}")
for g in out:
    if g["closing"]:
        pl = "0 top prizes left" if g["prizesLeft"] == 0 else "prizes unclaimed"
        print(f"    CLOSING #{g['no']:<5} {g['name'][:30]:<32} ends {g['endDate']}  ({pl})")
