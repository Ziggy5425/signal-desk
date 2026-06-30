#!/usr/bin/env python3
"""HTTP buyer for the running Signal Desk (run_seller.py @ 127.0.0.1:8800).

Mints a test-mode Shared Payment Token and pays the seller's 402, so the live
ledger view updates. A premium buy makes the seller pay a data vendor — which
pauses for your approval (the approval URL prints in the seller's terminal).

Usage:  .venv/bin/python buyer_http.py NVDA [--premium]
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SELLER = os.path.join(HERE, "seller")
for line in open(os.path.join(SELLER, ".env")):
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


code, _ = get()
print(f"[1] buyer requests {TICKER} unpaid  -> {code} (payment required)")

spt = post("/test_helpers/shared_payment/granted_tokens", {
    "payment_method": "pm_card_visa", "usage_limits[currency]": "usd",
    "usage_limits[max_amount]": "500", "usage_limits[expires_at]": str(int(time.time()) + 3600),
})["id"]
print(f"[2] buyer mints a Shared Payment Token -> {spt}")

label = "PREMIUM (will pause for the seller's spend approval)" if PREMIUM else "standard"
print(f"[3] buyer pays for {label} {TICKER} …")
code, body = get({"X-Shared-Payment-Token": spt})
print(f"[3] -> {code}")
print(json.dumps(body, indent=2))
