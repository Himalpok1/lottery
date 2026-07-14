#!/usr/bin/env python3
"""
PIN recovery — for when everyone's locked out of the Backend.

There's no email or SMS here to send a reset link to (the whole point of this app is
that it runs on your own machine with no accounts service anywhere else), so recovery
means being at the machine that runs server.py, or having its board-state.json in hand.

Stop server.py before running this, then start it again after — the running server
keeps the board in memory and won't notice a change to board-state.json on disk.

Run:   python3 reset_pin.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from server import load_state, save_state  # noqa: E402


def main():
    state = load_state()
    if not state:
        print("No board-state.json found here (or it's empty) — nothing to recover.")
        sys.exit(1)
    accounts = state.get("accounts") or []
    if not accounts:
        print("No accounts saved on this board — the app already shows the owner")
        print("setup screen (Create the owner login) next time it's opened.")
        sys.exit(0)

    print("\nAccounts on this board:\n")
    for i, a in enumerate(accounts):
        print(f"  {i + 1}. {a.get('name') or '(no name)'} — {a.get('phone')} — {a.get('role')}")
    wipe_choice = len(accounts) + 1
    print(f"  {wipe_choice}. Wipe ALL accounts (start over with the owner setup screen)\n")

    try:
        n = int(input("Pick a number: ").strip())
    except ValueError:
        print("Not a number.")
        sys.exit(1)

    if n == wipe_choice:
        if input("This removes every login on this board. Type YES to confirm: ").strip() != "YES":
            print("Cancelled.")
            return
        state["accounts"] = []
        save_state(state)
        print("Done — every device shows the owner setup screen next time it opens.")
        return

    if not (1 <= n <= len(accounts)):
        print("No such account.")
        sys.exit(1)

    acc = accounts[n - 1]
    new_pin = input(f"New 4-6 digit PIN for {acc.get('name') or acc.get('phone')}: ").strip()
    if not new_pin.isdigit() or not (4 <= len(new_pin) <= 6):
        print("PIN must be 4-6 digits.")
        sys.exit(1)
    acc["pin"] = new_pin
    save_state(state)
    print(f"Done — {acc.get('name') or acc.get('phone')} can sign in with the new PIN.")
    print("Restart server.py (or redeploy) if it's currently running.")


if __name__ == "__main__":
    main()
