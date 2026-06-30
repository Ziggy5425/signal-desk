#!/usr/bin/env python3
"""Prove the EARN loop against test-mode Stripe in one shot — no buyer infra.

Flow (verified, primary: docs.stripe.com/agentic-commerce SPT seller):
  1. Mint a chargeable test SPT against our own account via the test helper.
  2. Charge it by creating a PaymentIntent referencing the granted token.
  3. Print only statuses/ids (never the secret key).

Uses raw HTTP (urllib) against the verified endpoints, so it doesn't depend on
the installed `stripe` SDK's attribute paths. Reads STRIPE_SECRET_KEY from env
(or seller/.env). REFUSES to run against a live key.

Run:  STRIPE_SECRET_KEY=sk_test_... python3 verify_stripe.py
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.stripe.com/v1"
VERSION = "2026-04-22.preview"


def _load_env() -> str:
    key = os.environ.get("STRIPE_SECRET_KEY")
    if not key:
        envf = os.path.join(os.path.dirname(__file__), "seller", ".env")
        if os.path.exists(envf):
            for line in open(envf):
                line = line.strip()
                if line.startswith("STRIPE_SECRET_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    if not key:
        sys.exit("No STRIPE_SECRET_KEY found (env or seller/.env).")
    if key.startswith("sk_live_"):
        sys.exit("REFUSING: that's a LIVE key. Use sk_test_ only.")
    if not key.startswith("sk_test_"):
        sys.exit("Key doesn't look like sk_test_ — aborting to be safe.")
    return key


def _post(path: str, key: str, params: dict) -> dict:
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(API + path, data=data, method="POST")
    req.add_header("Authorization", "Basic " + base64.b64encode(f"{key}:".encode()).decode())
    req.add_header("Stripe-Version", VERSION)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  HTTP {e.code} on {path}:\n  {body}")
        raise


def main() -> None:
    key = _load_env()
    print("key: sk_test_… ok (live-key guard passed)")

    print("\n[1/2] minting test-mode Shared Payment Token (granted_token)…")
    spt = _post("/test_helpers/shared_payment/granted_tokens", key, {
        "payment_method": "pm_card_visa",
        "usage_limits[currency]": "usd",
        "usage_limits[max_amount]": "200",
        "usage_limits[expires_at]": str(int(time.time()) + 3600),
    })
    spt_id = spt.get("id", "")
    print(f"  -> {spt.get('object')} {spt_id}")

    print("\n[2/2] charging it via a PaymentIntent…")
    pi = _post("/payment_intents", key, {
        "amount": "200",
        "currency": "usd",
        "payment_method_data[shared_payment_granted_token]": spt_id,
        "confirm": "true",
    })
    print(f"  -> PaymentIntent {pi.get('id')} status={pi.get('status')}")

    if pi.get("status") == "succeeded":
        print("\n✅ EARN LOOP PROVEN: test SPT minted + charged $2.00 (test mode). "
              "Shared-Payment-Token preview is enabled on this account.")
    else:
        print(f"\n⚠️  Charge not 'succeeded' (status={pi.get('status')}). "
              "Inspect the PaymentIntent; preview may need enabling.")


if __name__ == "__main__":
    main()
