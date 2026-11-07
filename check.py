#!/usr/bin/env python3
"""Switch 2 Zelda 40th Anniversary stock check, run by GitHub Actions.

Reads schema.org availability from the Nintendo Store page and messages Dre on
Telegram when it looks purchasable, or when the check keeps failing (so a dead
watcher is never silent). Secrets: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
State (failure counter) lives in state.json, carried between runs by actions/cache.
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request

URL = ("https://www.nintendo.com/us/store/products/"
       "nintendo-switch-2-the-legend-of-zelda-40th-anniversary-edition-121642/")
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")
FAIL_ALERT_AT = 6        # ~30 min of failed checks at a 5-min schedule
FAIL_REPEAT_EVERY = 144  # then remind about every ~12 h while still failing

IN_STOCK = ("InStock", "LimitedAvailability", "PreOrder", "OnlineOnly", "BackOrder", "PreSale")
OUT = ("OutOfStock", "SoldOut", "Discontinued")


def load_state():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"fails": 0, "last": None}


def save_state(s):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(s, f)


def fetch():
    req = urllib.request.Request(URL, headers={
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
    })
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "replace")


def classify(html):
    """Return 'in', 'out' or 'unknown' from schema.org availability values."""
    vals = re.findall(r'availability\\*"\s*:\s*\\*"https?:(?:\\?/){2}schema\.org\\?/(\w+)', html)
    if not vals:
        return "unknown"
    if any(v in IN_STOCK for v in vals):
        return "in"
    if all(v in OUT for v in vals):
        return "out"
    return "unknown"


def telegram(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat:
        print("ERROR: missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID secret; alert not sent.")
        sys.exit(1)
    data = urllib.parse.urlencode({"chat_id": chat, "text": text,
                                   "disable_web_page_preview": "true"}).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage",
                                data=data, timeout=20) as r:
        ok = json.load(r).get("ok")
    print("Telegram sent." if ok else "ERROR: Telegram did not accept the message.")
    if not ok:
        sys.exit(1)


def main():
    if os.environ.get("TEST_ALERT") == "true":
        telegram("Prueba: el chequeo de stock de Switch 2 Zelda ya corre en GitHub (funciona con la PC apagada).")

    st = load_state()
    try:
        status, err = classify(fetch()), None
    except Exception as e:  # network error, 403, timeout...
        status, err = "unknown", str(e)[:150]
    print(f"status={status}" + (f" error={err}" if err else ""))

    if status == "in":
        st.update(fails=0, last="in")
        save_state(st)
        telegram("DISPONIBLE: Nintendo Switch 2 Zelda 40th Anniversary Edition parece estar EN STOCK.\n" + URL)
        return
    if status == "out":
        st.update(fails=0, last="out")
        save_state(st)
        return

    st["fails"] = st.get("fails", 0) + 1
    st["last"] = "unknown"
    save_state(st)
    n = st["fails"]
    if n == FAIL_ALERT_AT or (n > FAIL_ALERT_AT and (n - FAIL_ALERT_AT) % FAIL_REPEAT_EVERY == 0):
        telegram("Aviso: el chequeo de stock de Switch 2 Zelda (GitHub) no puede leer la pagina de Nintendo "
                 f"hace {n} intentos ({err or 'sin dato de disponibilidad'}). Revisa manualmente:\n" + URL)


if __name__ == "__main__":
    main()
