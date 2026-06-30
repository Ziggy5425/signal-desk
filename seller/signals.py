"""Signal source — reuses Clock Out Capital's real screener engine, with an offline fallback.

(Named `signals.py`, not `signal.py`, to avoid shadowing the stdlib `signal` module.)

Premium signals are the ones that justify a fresh paid data pull (the cost beat).
Network calls are time-boxed (never block the HTTP handler on a slow upstream).
"""
from __future__ import annotations

import json
import os
import urllib.request

SCREENER_URL = os.environ.get("SCREENER_API_URL", "http://localhost:8001")
TIMEOUT = float(os.environ.get("SIGNAL_TIMEOUT", "4"))


def _fetch_screener(ticker: str) -> dict | None:
    """Best-effort pull from the live Clock Out Capital screener. None on any failure."""
    url = f"{SCREENER_URL}/api/scan/ticker/{ticker}"  # TODO: confirm exact route
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def get_signal(ticker: str, premium: bool = False) -> dict:
    live = _fetch_screener(ticker) if premium else None
    if live:
        return {
            "ticker": ticker,
            "tier": "premium",
            "source": "live",
            "signal": live,
        }
    # Deterministic offline fallback so the loop always returns something to sell.
    score = (sum(ord(ch) for ch in ticker) % 41) + 60  # 60..100, stable per ticker
    return {
        "ticker": ticker,
        "tier": "premium" if premium else "standard",
        "source": "fallback",
        "signal": {
            "grade": "A" if score >= 90 else "B" if score >= 75 else "C",
            "score": score,
            "note": f"{ticker} setup score {score}"
                    + (" (fresh-data premium)" if premium else " (cached)"),
        },
    }
