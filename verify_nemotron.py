#!/usr/bin/env python3
"""Confirm the NVIDIA Nemotron 3 Ultra reasoning lane (OpenAI-compatible, raw HTTP)."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
for line in open(os.path.join(HERE, "seller", ".env")):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

KEY = os.environ.get("NVIDIA_API_KEY", "")
BASE = os.environ.get("NEMOTRON_BASE_URL", "https://integrate.api.nvidia.com/v1")
MODEL = os.environ.get("NEMOTRON_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")

if not KEY or "xxx" in KEY:
    raise SystemExit("NVIDIA_API_KEY not set in seller/.env")

payload = {
    "model": MODEL,
    "messages": [{"role": "user",
                  "content": "In one sentence, summarize this trading signal for a buyer: "
                             "NVDA, grade C, setup score 70."}],
    "max_tokens": 120,
    "temperature": 0.2,
    "chat_template_kwargs": {"enable_thinking": False},
}
import time


def call() -> dict:
    req = urllib.request.Request(BASE.rstrip("/") + "/chat/completions",
                                 data=json.dumps(payload).encode(), method="POST")
    req.add_header("Authorization", "Bearer " + KEY)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


for attempt in range(1, 6):
    try:
        data = call()
        msg = data["choices"][0]["message"].get("content") or "(empty)"
        print(f"✅ Nemotron lane OK  ({MODEL})  [attempt {attempt}]")
        print("  rationale:", msg.strip()[:300])
        break
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        if e.code == 503 and attempt < 5:
            print(f"  503 capacity (attempt {attempt}) — backing off…")
            time.sleep(3 * attempt)
            continue
        print(f"HTTP {e.code} from {BASE}: {body}")
        break
