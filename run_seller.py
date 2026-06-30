#!/usr/bin/env python3
"""Launch the Signal Desk seller as a real local server (loopback only).

Appends seller/ to sys.path AFTER stdlib so a stray signal.py can't shadow the
stdlib `signal` module. Open http://127.0.0.1:8800/ for the live ledger view.

Run:  .venv/bin/python run_seller.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SELLER = os.path.join(HERE, "seller")

for line in open(os.path.join(SELLER, ".env")):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())
sys.path.append(SELLER)

import uvicorn  # noqa: E402
import app      # noqa: E402  (seller/app.py)

if __name__ == "__main__":
    uvicorn.run(app.app, host="127.0.0.1", port=int(os.environ.get("SELLER_PORT", "8800")))
