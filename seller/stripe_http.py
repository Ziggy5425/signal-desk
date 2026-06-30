"""Tiny raw-HTTP Stripe client (stdlib only) — the proven path from verify_stripe.py.

Avoids the stripe SDK's preview-attribute uncertainty; the HTTP endpoints + params
are the verified part. Never logs the secret key.
"""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.stripe.com/v1"
VERSION = "2026-04-22.preview"


def post(path: str, params: dict, key: str | None = None, timeout: float = 30) -> dict:
    key = key or os.environ["STRIPE_SECRET_KEY"]
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(API + path, data=data, method="POST")
    req.add_header("Authorization", "Basic " + base64.b64encode(f"{key}:".encode()).decode())
    req.add_header("Stripe-Version", VERSION)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Stripe {e.code} on {path}: {e.read().decode()}") from None
