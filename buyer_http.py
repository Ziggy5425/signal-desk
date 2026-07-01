#!/usr/bin/env python3
"""HTTP buyer for the running Signal Desk (run_seller.py @ 127.0.0.1:8800).

Mints a test-mode Shared Payment Token and pays the seller's 402, so the live
ledger view updates. A premium buy makes the seller pay the signal's creator — a
payout that crosses the $600/W-9 line pauses for your approval (URL prints in the
seller's terminal).

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

label = "PREMIUM (creator signal — may pause for a W-9 payout approval)" if PREMIUM else "standard"
print(f"[3] buyer pays for {label} {TICKER} …")
code, body = get({"X-Shared-Payment-Token": spt})
print(f"[3] -> {code}")

if code == 200:
    sig = body.get("signal", {})
    out = {"ticker": body.get("ticker"), "tier": body.get("tier"),
           "grade": sig.get("grade"), "score": sig.get("score"),
           "paid_cents": body.get("paid_cents")}
    if PREMIUM:
        out.update({"creator": body.get("creator"),
                    "payout_cents": body.get("creator_payout_cents"),
                    "payout_mode": body.get("spend_mode"),
                    "auto_payout_left_cents": body.get("budget_remaining_cents"),
                    "reasoning_tier": body.get("reasoning_tier"),
                    "rationale": body.get("rationale")})
    print(json.dumps(out, indent=2))
    if PREMIUM:
        brain = ("paid NVIDIA Nemotron 550B (hard call)"
                 if body.get("reasoning_tier") == "nemotron-550b" else "free local read")
        print(f"[4] earned ${body.get('paid_cents', 0) / 100:.2f} · paid creator "
              f"{body.get('creator')} ${body.get('creator_payout_cents', 0) / 100:.2f} "
              f"{body.get('spend_mode')} · reasoning: {brain} · "
              f"allowance left ${body.get('budget_remaining_cents', 0) / 100:.2f}")
else:
    print(json.dumps(body, indent=2))
