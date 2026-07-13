#!/usr/bin/env python3
"""
Lottery Display - local server (no dependencies).

Run:   python3 server.py
Stop:  Ctrl+C

Serves the board to every device on your Wi-Fi AND holds the board's data, so the
TV on the wall and the counter app on your phone are looking at the same board.

  http://<this-machine-ip>:8000/index.html            <- the TV board
  http://<this-machine-ip>:8000/index.html#counter    <- the clerk's phone
  http://<this-machine-ip>:8000/index.html#admin      <- the backend

The board is stored in board-state.json next to this script. Back it up like any file.
"""
import http.server
import socketserver
import webbrowser
import threading
import socket
import json
import re
import os
import sys
import hashlib
import urllib.request
import urllib.parse

PORT = int(os.environ.get("PORT", "8000"))
PIN = os.environ.get("PIN", "0987")
STATE_FILE = "board-state.json"
ART_DIR = "art"
ART_BASE = "https://www.texaslottery.com/export/sites/lottery/Images/scratchoffs/"
# Sent when we go and get a picture. State sites often refuse a request that arrives with
# no referrer or no user-agent (that's what "hotlink protection" is), so we send both.
ART_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer": "https://www.texaslottery.com/export/sites/lottery/Games/Scratch_Offs/index.html",
    "Accept": "image/avif,image/webp,image/gif,image/png,*/*",
}


def fetch_art(no):
    """Download one ticket picture. Returns (bytes, extension)."""
    last = None
    for ext in ("gif", "png", "jpg"):
        url = f"{ART_BASE}{no}_200X200.{ext}"
        try:
            req = urllib.request.Request(url, headers=ART_HEADERS)
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
            if data and len(data) > 200:  # anything smaller is an error page, not art
                return data, ext
        except Exception as e:
            last = e
    raise RuntimeError(f"no image found for #{no} ({last})")


_lock = threading.Lock()
_rev = 0


def load_state():
    global _rev
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                d = json.load(f)
            _rev = d.get("rev", 0)
            return d.get("state")
        except Exception:
            pass
    return None


_state = load_state()


def save_state(state):
    """Persist the board and bump the revision so other devices notice."""
    global _rev, _state
    with _lock:
        _rev += 1
        _state = state
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"rev": _rev, "state": state}, f)
        os.replace(tmp, STATE_FILE)  # atomic: never leave a half-written file
        return _rev


class Handler(http.server.SimpleHTTPRequestHandler):
    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # /api/rev is tiny - devices poll it to ask "has anything changed?"
        if self.path.startswith("/api/rev"):
            return self._json({"rev": _rev})
        if self.path.startswith("/api/state"):
            return self._json({"rev": _rev, "state": _state})
        # Ticket art, served from our own machine.
        # texaslottery.com can refuse hotlinked images, and the TV may have no internet at
        # all — so we fetch each picture once, keep it in art/, and serve it from here.
        m = re.match(r"/art/(\d{3,5})\.(gif|png|jpg)", self.path)
        if m:
            return self._art(m.group(1))
        if self.path.startswith("/api/art"):   # pre-download every picture
            if self.headers.get("X-Pin") != PIN:
                return self._json({"error": "wrong pin"}, 401)
            return self._cache_all()
        # Any other linked picture (an ad, a logo, a background). Same story as the ticket
        # art: the source may refuse a hotlinked request, and the TV may be offline. So we
        # fetch it once, cache it, and serve it from here.
        if self.path.startswith("/api/img"):
            q = urllib.parse.urlparse(self.path).query
            url = urllib.parse.parse_qs(q).get("u", [""])[0]
            return self._proxy_img(url)
        # The browser can't read texaslottery.com (no CORS headers), but we can.
        if self.path.startswith("/api/tx"):
            if self.headers.get("X-Pin") != PIN:
                return self._json({"error": "wrong pin"}, 401)
            try:
                import tx_fetch
                games, note = tx_fetch.fetch_all()
                with open("tx-scratchoffs.json", "w") as f:
                    json.dump(games, f, indent=1)
                print(f"  [tx] fetched live from texaslottery.com — {note}")
                return self._json({"ok": True, "note": note, "games": games})
            except Exception as e:
                print(f"  [tx] fetch failed: {e}")
                return self._json({"ok": False, "error": str(e)}, 502)
        return super().do_GET()

    def _art(self, no):
        """Serve a ticket picture, downloading it the first time we're asked."""
        os.makedirs(ART_DIR, exist_ok=True)
        for ext in ("gif", "png", "jpg"):
            path = os.path.join(ART_DIR, f"{no}.{ext}")
            if os.path.exists(path) and os.path.getsize(path) > 0:
                return self._send_file(path, ext)
        try:
            data, ext = fetch_art(no)
        except Exception as e:
            print(f"  [art] #{no} unavailable: {e}")
            return self._json({"error": "art unavailable"}, 404)
        path = os.path.join(ART_DIR, f"{no}.{ext}")
        with open(path, "wb") as f:
            f.write(data)
        return self._send_file(path, ext)

    def _proxy_img(self, url):
        """Fetch and cache any linked picture."""
        if not url or not url.startswith(("http://", "https://")):
            return self._json({"error": "bad url"}, 400)
        key = hashlib.sha1(url.encode()).hexdigest()[:16]
        os.makedirs(ART_DIR, exist_ok=True)
        for ext in ("gif", "png", "jpg", "webp"):
            p = os.path.join(ART_DIR, f"link_{key}.{ext}")
            if os.path.exists(p) and os.path.getsize(p) > 0:
                return self._send_file(p, ext)
        try:
            parts = urllib.parse.urlsplit(url)
            # Hotlink checks vary: some want a referrer from the picture's own site, some
            # want none at all. Try the likely ones rather than failing on the first 403.
            attempts = [
                f"{parts.scheme}://{parts.netloc}/",   # same-origin referrer (most common)
                ART_HEADERS["Referer"],                # the lottery's own page
                None,                                  # no referrer at all
            ]
            data = ctype = None
            last = None
            for ref in attempts:
                hdrs = dict(ART_HEADERS)
                if ref:
                    hdrs["Referer"] = ref
                else:
                    hdrs.pop("Referer", None)
                try:
                    req = urllib.request.Request(url, headers=hdrs)
                    with urllib.request.urlopen(req, timeout=20) as r:
                        data = r.read()
                        ctype = r.headers.get("Content-Type", "")
                    if data and len(data) >= 100:
                        break
                    data = None
                except Exception as e:
                    last = e
            if not data:
                raise RuntimeError(last or "empty response")
            ext = ("gif" if "gif" in ctype else "png" if "png" in ctype
                   else "webp" if "webp" in ctype else "jpg")
            p = os.path.join(ART_DIR, f"link_{key}.{ext}")
            with open(p, "wb") as f:
                f.write(data)
            return self._send_file(p, ext)
        except Exception as e:
            print(f"  [img] could not load {url[:60]}: {e}")
            return self._json({"error": "image unavailable"}, 404)

    def _send_file(self, path, ext):
        data = open(path, "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", f"image/{'jpeg' if ext == 'jpg' else ext}")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=86400")
        super(http.server.SimpleHTTPRequestHandler, self).end_headers()
        self.wfile.write(data)

    def _cache_all(self):
        """Download every picture in the catalog so the TV works with no internet."""
        try:
            with open("tx-scratchoffs.json") as f:
                games = json.load(f)
        except Exception as e:
            return self._json({"ok": False, "error": f"no catalog: {e}"}, 500)
        os.makedirs(ART_DIR, exist_ok=True)
        got = cached = failed = 0
        for g in games:
            no = str(g.get("no", ""))
            if not no:
                continue
            if any(os.path.exists(os.path.join(ART_DIR, f"{no}.{e}")) for e in ("gif", "png", "jpg")):
                cached += 1
                continue
            try:
                data, ext = fetch_art(no)
                with open(os.path.join(ART_DIR, f"{no}.{ext}"), "wb") as f:
                    f.write(data)
                got += 1
            except Exception:
                failed += 1
        print(f"  [art] downloaded {got}, already had {cached}, failed {failed}")
        return self._json({"ok": True, "downloaded": got, "cached": cached, "failed": failed,
                           "total": got + cached})

    def do_POST(self):
        if not self.path.startswith("/api/state"):
            return self._json({"error": "unknown endpoint"}, 404)
        if self.headers.get("X-Pin") != PIN:
            return self._json({"error": "wrong pin"}, 401)
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n > 32 * 1024 * 1024:
                return self._json({"error": "too large"}, 413)
            body = json.loads(self.rfile.read(n))
            rev = save_state(body.get("state"))
            return self._json({"rev": rev})
        except Exception as e:
            return self._json({"error": str(e)}, 400)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()

    def log_message(self, *args):
        pass


def lan_ip():
    """The address other devices on the Wi-Fi should use."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # sends nothing; just picks the outbound interface
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.exists("index.html"):
        print("ERROR: index.html not found next to server.py")
        sys.exit(1)

    port = PORT
    httpd = None
    for _ in range(50):
        try:
            # 0.0.0.0 = listen on every network interface, so the TV can reach us
            httpd = Server(("0.0.0.0", port), Handler)
            break
        except OSError:
            port += 1
    if httpd is None:
        print("ERROR: no free port. Try: PORT=9000 python3 server.py")
        sys.exit(1)

    ip = lan_ip()
    print("=" * 62)
    print("  Lottery Display is running")
    print()
    print(f"  On this machine:    http://localhost:{port}/index.html")
    print()
    print(f"  On the TV:          http://{ip}:{port}/index.html")
    print(f"  Counter app:        http://{ip}:{port}/index.html#counter")
    print(f"  Backend:            http://{ip}:{port}/index.html#admin")
    print()
    print(f"  Board saved to      {STATE_FILE}  (rev {_rev})")
    print("  Leave this window open. Ctrl+C to stop.")
    print("=" * 62)

    threading.Timer(0.6, lambda: webbrowser.open(f"http://localhost:{port}/index.html")).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped. The board is saved.")
        httpd.shutdown()


if __name__ == "__main__":
    main()
