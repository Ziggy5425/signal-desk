#!/usr/bin/env python3
"""Buy a signal from the running Signal Desk and print ONE concise result line.

Used by the Hermes `signal-desk-buyer` skill: a Hermes agent runs this via its
terminal tool and relays the output. Pure stdlib — no venv needed.

Usage:  python3 agent_buy.py TICKER [--premium]
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SELLER = HERE + "/seller"
_envfile = SELLER + "/.env"
if os.path.exists(_envfile):
    for line in open(_envfile):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
sys.path.append(SELLER)
from stripe_http import post  # noqa: E402

BASE = os.environ.get("SELLER_BASE", "http://127.0.0.1:8800")
TICKER = (sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "NVDA").upper()
PREMIUM = "--premium" in sys.argv
url = f"{BASE}/signal/{TICKER}" + ("?premium=true" if PREMIUM else "")


def get(headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=400) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


get()  # 402 (payment required)
spt = post("/test_helpers/shared_payment/granted_tokens", {
    "payment_method": "pm_card_visa", "usage_limits[currency]": "usd",
    "usage_limits[max_amount]": "500", "usage_limits[expires_at]": str(int(time.time()) + 3600),
})["id"]
code, body = get({"X-Shared-Payment-Token": spt})
if code != 200:
    print(f"PURCHASE FAILED ({code}): {body}")
    sys.exit(1)

s = body.get("signal", {})
out = (f"Bought {body.get('tier')} signal for {TICKER} at ${body.get('paid_cents', 0)/100:.2f} "
       f"(paid via Stripe Shared Payment Token). Grade {s.get('grade')}, score {s.get('score')}.")
if PREMIUM:
    out += (f" To serve it the desk bought data {body.get('spend_mode')} "
            f"(autonomous budget left ${body.get('budget_remaining_cents', 0)/100:.2f}).")
    if body.get("rationale"):
        out += f" Nemotron analyst note: {body['rationale']}"
print(out)
