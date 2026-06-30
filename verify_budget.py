#!/usr/bin/env python3
"""Probe SPT usage_limits semantics: can ONE granted_token (a human-authorized
budget) be charged MULTIPLE times up to max_amount? Decides the budget design."""
from __future__ import annotations

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
for line in open(os.path.join(HERE, "seller", ".env")):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())
sys.path.append(os.path.join(HERE, "seller"))
from stripe_http import post  # noqa: E402

print("Minting ONE SPT budget: usage_limits.max_amount = $5.00 …")
spt = post("/test_helpers/shared_payment/granted_tokens", {
    "payment_method": "pm_card_visa",
    "usage_limits[currency]": "usd",
    "usage_limits[max_amount]": "500",
    "usage_limits[expires_at]": str(int(time.time()) + 3600),
})["id"]
print(f"  budget SPT: {spt}\n")

cumulative = 0
for i, amt in enumerate([200, 200, 200], 1):  # 2 + 2 + 2 = $6 vs the $5 cap
    cumulative += amt
    try:
        pi = post("/payment_intents", {
            "amount": str(amt), "currency": "usd",
            "payment_method_data[shared_payment_granted_token]": spt,
            "confirm": "true",
        })
        print(f"  charge {i}: ${amt/100:.2f}  -> {pi.get('status')}  (cumulative ${cumulative/100:.2f} / $5.00 cap)")
    except Exception as e:
        print(f"  charge {i}: ${amt/100:.2f}  -> BLOCKED: {str(e)[:160]}")

print("\nReading: if charges 1+2 succeed and 3 is blocked -> ONE token = a reusable "
      "budget capped at max_amount (authentic). If only charge 1 works -> single-use "
      "(model the budget as a counter + mint per draw).")
