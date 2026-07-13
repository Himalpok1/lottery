# Lottery Display — the whole thing in one document

A digital scratch-off board for the TV at **Swing by Maypearl**, plus a phone app for the
clerk and a backend where you set it all up. It runs on your own machine. No accounts, no
subscription, no internet required once it's set up.

---

## 1. What's in this folder

| File | What it is | Touch it? |
|---|---|---|
| **index.html** | The whole app — TV board, counter app, and backend, in one file. | No |
| **server.py** | The server. Shares the board with every device on your Wi-Fi and fetches pictures. | No |
| **start-mac.command** | Double-click this on a Mac to run it. | Yes — this is your start button |
| **start-windows.bat** | Same, for Windows. | Yes |
| **tx_fetch.py** | Pulls the live game list from texaslottery.com. | No |
| **tx-scratchoffs.json** | The 74-game Texas catalog. Refreshed when you hit *Fetch live*. | No |
| **build_tx_catalog.py** | Rebuilds the catalog from hand-checked data. A backup for the scraper. | No |
| **PROJECT.md** | This document. | — |
| **README.md** | Shorter version of this. | — |

Two more appear on their own once you run it:

| File | What it is |
|---|---|
| **board-state.json** | 🔴 **Your board.** Games, slots, ads, jackpots, winners, sales. **This is your data.** |
| **art/** | Cached ticket pictures. Deleting it is harmless — it just re-downloads them. |

---

## 2. Starting it

**Mac:** double-click **`start-mac.command`**.

The first time, macOS will probably refuse: *"cannot be opened because it is from an
unidentified developer."* That's normal. **Right-click the file → Open → Open.** It'll
trust it from then on.

**Windows:** double-click **`start-windows.bat`**.

**Terminal, if you prefer:**
```bash
cd ~/Desktop/lottery
python3 server.py
```

A window opens and prints something like:

```
  Lottery Display is running

  On this machine:    http://localhost:8000/index.html
  On the TV:          http://192.168.1.42:8000/index.html
  Counter app:        http://192.168.1.42:8000/index.html#counter
  Backend:            http://192.168.1.42:8000/index.html#admin

  Board saved to      board-state.json  (rev 12)
```

**Leave that window open.** Closing it stops the board. Your browser opens automatically.

The `192.168.x.x` address is the one you type into the TV and your phone. It'll be different
on your network — use whatever it prints.

---

## 3. Moving it to another device

Everything is in this folder. To move the project:

1. **Stop the server** (Ctrl+C in that window, or just close it).
2. **Copy the whole `lottery` folder** to the new machine — AirDrop, a USB stick, whatever.
3. On the new machine, double-click `start-mac.command` again.

That's it. `board-state.json` travels with the folder, so your 40 games, slots, ads and sales
all come with it exactly as they were.

**Requirements on the new machine:** Python 3. Every Mac already has it. On Windows, install
it from python.org and **tick "Add Python to PATH"** during setup.

**If you only want the board, not the sales history:** copy everything except `board-state.json`
and you'll start fresh.

**Belt and braces:** the backend also has a **Back up** button that downloads the whole board as
a `.json` file, and **Restore** to load it back. Use that if you're moving between machines a lot.

---

## 4. The three screens

One app, three faces. You switch with the buttons on screen, or by the address:

| Screen | Address | Who it's for |
|---|---|---|
| **TV board** | `…/index.html` | The customer, looking at the wall |
| **Counter app** | `…/index.html#counter` | The clerk, on a phone |
| **Backend** | `…/index.html#admin` | You |

**The board lives on the host machine**, not in each browser. So the TV, the phone, and your
laptop are all looking at the *same* board — change something on the phone and the TV updates
itself in about a second.

**The status dot** tells you where you stand:

| Dot | Means |
|---|---|
| 🟢 **● live** | Talking to the host. Changes sync everywhere. |
| 🔴 **● offline** | Host is off, or Wi-Fi dropped. |
| ⚪ **● this device only** | You opened `index.html` as a plain file instead of through the server. Works, but the TV won't see your changes. |

---

## 5. The TV board

What the customer sees. 40 ticket cards, filling the screen with no scrolling.

### A card

```
   ┌──────────────────────┐
   │ 07                   │   ← SLOT NUMBER, in red. The thing the customer says out loud.
   │                      │
   │   [ ticket art ]     │   ← The state's own picture. It already has the price and
   │                      │      game number printed on it, so the card doesn't repeat them.
   │            ╲CLOSING  │   ← Red ribbon if the state has called the game.
   │             ╲ SOON   │
   ├──────────────────────┤
   │ GOOD LUCK   Current  │   ← Status, and which ticket you're on in the pack.
   │                  92  │
   ├──────────────────────┤
   │ ████████████████████ │   ← Price colour bar ($5 red, $10 purple, $20 gold…)
   └──────────────────────┘
```

### What the status line says, and when

| It reads | Because |
|---|---|
| **LAST CHANCE** | Zero top prizes remaining. |
| **ONLY 3 LEFT** | Top prizes are down to your threshold (3 by default). |
| **CLOSING SOON** | The state has called the game — the card also gets the red ribbon. |
| **GOOD LUCK** | Everything else. |

### The two numbers people mix up

- **Prizes left** — how many *top prizes* the state still shows for that game. Drives the red
  warnings above.
- **Current** — which *ticket in the open pack* you're selling. Just information for the customer.

They're different things and they live in different columns in the backend.

### Board buttons

Move the mouse and three buttons appear at the bottom right; they fade away after 3 seconds so
the wall stays clean.

- **Full screen** — do this once on the TV and leave it.
- **Counter app** / **Backend** — jump to the other screens.

---

## 6. The counter app (the clerk's phone)

Open `…#counter` on a phone. Big buttons. Tap one and **the TV changes instantly.**

### Show tickets on screen

| Button | What the TV does |
|---|---|
| **$1 / $2 / $5 / $10…** | Dims everything except that price. |
| **New tickets** | Only the ones flagged New. |
| **Lucky tickets** | Only the ones flagged Lucky. |
| **Ending tickets** | Only the ones running out or closing. |
| **Recommended game** | Full-screen spotlight of the best game — the most top prizes still out there per dollar of ticket price. |
| **Recommended slots** | Highlights the slots still holding prizes. |
| **Ticket on number** | Type a slot or game number → the TV spotlights that ticket, full screen. |
| **Show all 40** | Back to the full board. |

**It puts itself back.** A pushed view holds for 30 seconds, then the board returns to all 40 on
its own. The clerk never has to remember to reset it.

### Log a sale

Tap a price to record one ticket sold. It lands in the backend's Sales tab. That's the whole
workflow — no forms.

---

## 7. The backend

Where you set everything up. Eight tabs.

### Games

The 40 slots. Each row:

| Column | What goes in it |
|---|---|
| **Slot** | Its spot on the wall. ▲▼ arrows nudge a game up or down one slot. |
| **Game no.** | The number printed on the ticket. |
| **Game name** | |
| **Price** | $1 → $100. Sets the colour bar. |
| **Prizes left** | Top prizes remaining → drives ONLY N LEFT / LAST CHANCE. |
| **Current** | The ticket you're on in the open pack. |
| **Flags** | New · Lucky · Closing |
| **Swap** | **Swap with…** trades any two slots. Nothing is overwritten — the two games change places. |
| **Picture** | **Choose** a file, or **Link** an image URL. |

### Branding

Display title, subtitle, **logo** (upload or link), columns on the TV (8 across gives you exactly
8 × 5 = 40 with no scrolling), sort order, the "ending" threshold, and **tile style** — Ticket
cards (default) or the older Rack slots look.

### Theme

Seven looks. Default is **White & Red**. Also **Red & White** (red board, white type), Midnight
Rack, Neon Carnival, Blue Chip, Table Felt, Crimson Rush — plus any accent colour you like.

Background can be the theme colour, an uploaded image, or a looping video by link.

*The backend itself stays red and white no matter which board theme you pick.*

### Advertisements

Picture + kicker + message, rotating in the rail beside the tickets. Set how many seconds each
one holds. "2 hot dogs for $3" — advertise where you know people are looking.

### Jackpots

Game, amount, next draw. Shows in a strip under the header. **Typed in by hand** — see the honest
limits at the bottom.

### Winners

Name, game, amount. Builds local buzz in the rail. "Dave R. — Lady Luck 7s — $5,000."

### Sales

Today / this month / this year, tickets and revenue, broken down by price. **Export CSV.**
Fed by the clerk tapping Log a sale.

### Stores & managers

Run more than one store, each with its own board. Manager list with PINs.

### Lottery data

The Texas Lottery catalog — all **74 current games**, with art.

- **Add to slot…** — every game has a slot dropdown. *You* pick which slot it goes in. Occupied
  slots show what's in them, and it asks before replacing anything.
- **Swap to slot…** — for a game already up. The two slots trade places.
- **Auto-fill the 40** — one click: new games first, then featured, then a spread across every
  price point.
- **Fetch live from texaslottery.com** — pulls the current list straight from the state. Games on
  your board update in place; your slots, typed prizes and Current numbers are left alone.
- **Download all ticket art** — grabs all 74 pictures onto your machine. **Do this once** and the
  TV never needs the internet for pictures again.

---

## 8. Putting it on the TV

Everything must be on the same Wi-Fi. Open `http://<host-ip>:8000/index.html` on the TV, press
**Full screen**, leave it.

| Option | Verdict |
|---|---|
| **Raspberry Pi** (~$60) | The one I'd pick. Chromium in kiosk mode, boots straight into the board, runs for months. It can be the host *and* the TV player — one box does everything. |
| **Any mini PC / old laptop** | Zero setup. HDMI into the TV, browser full-screen. |
| **Fire TV Stick** (~$30) | Cheapest that works. Use the Silk browser. **Turn off sleep** or it drops the page. |
| **The TV's own browser** | Most Samsung/LG sets have one. No extra hardware. Older ones stutter with 40 pictures. |
| **Roku** | Don't. No usable browser. |

**Two things that will bite you if you skip them:**

1. **Reserve a static IP for the host** in your router settings. Otherwise the address changes
   when the router reboots and the TV shows nothing.
2. **Set the TV device to never sleep.**

---

## 9. Why pictures work the way they do

Texas Lottery **refuses hotlinked images** — when a browser asks for a ticket picture directly,
their server sends back a 403 and you get a blank tile. That's deliberate on their end.

So the server fetches pictures instead of your browser. It downloads each one properly, caches it
in `art/`, and serves it from your own machine. Same for any picture you add with **Link**.

Three consequences worth knowing:

- **Hit "Download all ticket art" once.** Then the board works with the internet completely off.
- If a picture ever fails, the tile shows the price and game number rather than a broken image.
- **Fetch live** and **Link** only work when you're running through `server.py` — a plain
  double-clicked `index.html` can't reach texaslottery.com.

---

## 10. What this does not do

Three things a paid service would do that this honestly doesn't:

- **Live jackpot amounts.** They're typed in by hand. Keeping them live needs a scheduled job.
- **Prizes-remaining that updates itself.** The state doesn't publish it in any list — it's on
  each game's individual detail page. The one exception: games closing with **zero** top prizes
  come through automatically as LAST CHANCE.
- **Managing the board from anywhere in the world.** That needs real hosting. What you get today
  is the whole shop: any device on your Wi-Fi, sharing one live board.

The first two are a scraper away. Ask if you want them.

---

## 11. Quick fixes

| Problem | Fix |
|---|---|
| Pictures are blank | Backend → Lottery data → **Download all ticket art**. |
| TV shows nothing | Is the server window still open? Is the TV on the same Wi-Fi? Is the IP still right? |
| Phone doesn't change the TV | Check the status dot. ⚪ *this device only* means you opened the file directly instead of through the server. |
| Changes vanished | You were on ⚪ *this device only*. Run it through `start-mac.command`. |
| macOS won't open the launcher | Right-click → **Open** → **Open**. |
| Port 8000 is busy | It picks the next free one automatically — read the address it prints. |
| Board is gone | `board-state.json` is your data. Restore a backup, or the folder from your other machine. |
