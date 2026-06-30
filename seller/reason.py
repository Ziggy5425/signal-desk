"""Nemotron 3 Ultra rationale for a sold signal — educational framing, graceful fallback.

Keeps to descriptive/educational language (no buy/sell call, no guarantees). Returns
"" on any error so a slow/busy model never blocks the sale.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

BASE = os.environ.get("NEMOTRON_BASE_URL", "https://integrate.api.nvidia.com/v1")
MODEL = os.environ.get("NEMOTRON_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")
KEY = os.environ.get("NVIDIA_API_KEY", "")


def rationale(sig: dict, timeout: float = 20) -> str:
    if not KEY or "xxx" in KEY:
        return ""
    s = sig.get("signal", {})
    prompt = (
        "You are an educational markets analyst. In ONE concise, descriptive sentence, "
        "explain what this technical setup indicates. Educational only — no buy/sell "
        f"recommendation and no guarantees. Signal: {sig.get('ticker')} "
        f"grade {s.get('grade')}, setup score {s.get('score')}."
    )
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100,
        "temperature": 0.3,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(BASE.rstrip("/") + "/chat/completions",
                                 data=json.dumps(payload).encode(), method="POST")
    req.add_header("Authorization", "Bearer " + KEY)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode())
        return (d["choices"][0]["message"].get("content") or "").strip()
    except Exception:
        return ""
