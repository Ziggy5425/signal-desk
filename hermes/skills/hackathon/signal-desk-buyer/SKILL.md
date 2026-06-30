---
name: signal-desk-buyer
description: "Buy a trading signal from the local Signal Desk by paying its HTTP-402."
version: 1.0.0
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [hackathon, trading, buyer, http, stripe]
    requires_toolsets: [terminal]
---

# Signal Desk buyer

The **Signal Desk** is a local HTTP API that sells trading signals and charges per call with a
Stripe Shared Payment Token. Use this skill whenever the user asks to **buy a signal**.

> Setup: this skill runs `agent_buy.py` from your clone of the Signal Desk repo. Set the
> `SIGNAL_DESK` environment variable to that checkout, e.g. `export SIGNAL_DESK=~/signal-desk`.

When asked to buy a signal, use the `terminal` tool to do exactly this:

1. Confirm the desk is up:
   ```bash
   curl -s http://127.0.0.1:8800/health
   ```
2. Buy the requested signal. Add `--premium` if the user wants the premium / Nemotron-analyzed tier:
   ```bash
   python3 "$SIGNAL_DESK/agent_buy.py" <TICKER> [--premium]
   ```
   For example: `python3 "$SIGNAL_DESK/agent_buy.py" NVDA --premium`
3. Report the script's output back to the user verbatim — the signal's grade and score, what was
   paid, and (for the premium tier) whether the desk's own data purchase was made **autonomously**
   from its budget or required a human approval, plus the Nemotron analyst note.

Default to ticker **NVDA** and the **premium** tier unless the user specifies otherwise.
