# Recording runbook — the autonomous demo, with a Hermes agent buyer

All on one box, loopback, test mode (no real money). Two layers of autonomy:
- **A Hermes agent** (reasoning on NVIDIA Nemotron) is the **buyer** — it decides to buy and pays the desk.
- **The desk** autonomously buys its own data within a human-set budget; a human approves only the
  over-budget exception.

Sizing for a tight take: budget **$1.50**, each data pull **$0.50** → 3 autonomous pulls, then the 4th escalates.

## Terminal 1 — the Signal Desk (seller + live ledger)
```bash
cd ~/projects/hermes-hackathon
pkill -f run_seller.py 2>/dev/null              # clear any stale seller on 8800
DATA_BUDGET_CENTS=150 LEDGER_DB=$PWD/take.db .venv/bin/python run_seller.py
```
Forward port 8800 (VS Code does it automatically) and open **http://127.0.0.1:8800/** — watch
**"Auto-budget left"** draw down. Leave this terminal visible; the **over-budget** pull prints
`💳 APPROVE THIS SPEND … <url>` here.

## Terminal 2 — the Hermes agent buyer
The hero shot — a real Hermes agent uses the skill to buy:
```bash
HERMES="HERMES_HOME=~/hermes-hack ~/projects/hermes/.venv/bin/hermes -z"
# the agent reasons, finds the signal-desk-buyer skill, pays the 402, reports back:
HERMES_HOME=~/hermes-hack ~/projects/hermes/.venv/bin/hermes -z "Use the signal-desk-buyer skill to buy a premium NVDA signal."
```
Run the agent on the snappier OpenRouter model if Nemotron lags — put `-m fast` **before** `-z`:
`HERMES_HOME=~/hermes-hack ~/projects/hermes/.venv/bin/hermes -m fast -z "Use the signal-desk-buyer skill to buy a premium NVDA signal."`

## Two ways to run the take

**A — all-Hermes (most authentic, slower).** Run the agent buy 4 times. The first three are autonomous
(budget drops $1.50→$1.00→$0.50→$0.00); on the 4th the desk hits the budget and **the agent pauses waiting
for your approval** — Terminal 1 prints the URL, you approve, the agent finishes. Narrate the pause: *"the
agent is waiting on me."*

**B — Hermes hero + fast drawdown (snappy, recommended for a tight video).**
1. One Hermes agent buy (above) — the headline: *"a Hermes agent, on NVIDIA Nemotron, is my buyer."*
2. Then drive the budget down fast with the scripted buyer (instant, deterministic):
   ```bash
   .venv/bin/python buyer_http.py NVDA --premium    # ×3 (autonomous), then:
   .venv/bin/python buyer_http.py NVDA --premium    # 4th → over budget → approve in Stripe Link
   ```

## Narration beats
See `DEMO.md`. Arc: **a Hermes agent runs the business** → it earns → it spends on data **autonomously**
within budget → on the exception it **asks a human** → net-positive, at scale.

## Notes
- The first Hermes turn loads model + skills; give it a few seconds. `-m fast` = OpenRouter (quicker).
- Nemotron's free tier can 503 — re-run if a turn errors.
- Fresh take = new `LEDGER_DB` name; budget resets on seller restart.

## Stop
- Ctrl+C Terminal 1.
