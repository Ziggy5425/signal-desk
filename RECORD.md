# Recording runbook — the autonomous creator marketplace

All on one box, loopback, test mode (no real money). The Signal Desk is an **autonomous
creator marketplace**: it sells creators' premium signals to buyer agents, and it runs its
own money on both sides —

- **Earns** from buyer agents (Stripe Shared Payment Tokens).
- **Pays creators** their rev-share **autonomously**, within an auto-approve allowance.
- **Pays for its own intelligence** — on a *hard* call it buys NVIDIA Nemotron 550B reasoning;
  easy calls use the free local read.
- **Escalates to a human ONLY** for the one thing that legally needs it: a creator payout that
  crosses the **IRS $600 / W-9** reporting line.

Sizing for a tight take: allowance **$1.50**, each creator payout **$0.50** → 3 autonomous
payouts, then the 4th crosses the line and asks you.

## Terminal 1 — the Signal Desk (seller + live ledger)
```bash
cd ~/projects/hermes-hackathon
PAYOUT_BUDGET_CENTS=150 LEDGER_DB=$PWD/final.db .venv/bin/python run_seller.py
```
Use a **fresh** DB name (`final.db`) so the ledger starts at $0. Forward port 8800 and open
**http://127.0.0.1:8800/** — watch **"Auto-payout left"** draw down and the rows tag
`earn` / `auto-payout` / `compute` / `W-9 approved`. The over-limit payout prints
`💳 APPROVE THIS CREATOR PAYOUT … <url>` **here**.

## Terminal 2 — the buyers
```bash
cd ~/projects/hermes-hackathon

# 1) HERO SHOT — a real Hermes agent (reasoning on NVIDIA Nemotron) is the buyer:
HERMES_HOME=~/hermes-hack ~/projects/hermes/.venv/bin/hermes -z "Use the signal-desk-buyer skill to buy a premium NVDA signal."
#    → buyer pays $2.00 · creator @QuantJane paid $0.50 (autonomous) · Nemotron hard-call reasoning
#    → allowance $1.50 → $1.00

# 2) & 3) drive the allowance down fast (deterministic, instant):
.venv/bin/python buyer_http.py NVDA --premium     # → $1.00 → $0.50  (autonomous payout)
.venv/bin/python buyer_http.py NVDA --premium     # → $0.50 → $0.00  (autonomous payout)

# 4) THE EXCEPTION — this payout crosses the $600/W-9 line, so it stops and asks you:
.venv/bin/python buyer_http.py NVDA --premium     # → prints APPROVE-CREATOR-PAYOUT URL in Terminal 1; PAUSES
```
On buy #4, **Terminal 1 prints `💳 APPROVE THIS CREATOR PAYOUT — @QuantJane crosses the $600/W-9
line …`** and the buy hangs. Open that URL, click **Approve** (test mode, card 4242 — no real
money), and it completes.

## 🎙 Narration (the arc)
1. **Open** (ledger $0, "Auto-payout left $1.50"): *"This is an autonomous business — a creator
   marketplace. It sells creators' signals, and it runs its own money: earning from buyers,
   paying creators, even paying for its own AI. I set one limit and it runs itself."*
2. **Hero buy:** *"My buyer is a real Hermes agent on NVIDIA Nemotron. It found a skill, paid my
   API with a Stripe token, and got @QuantJane's signal. And to serve it, the desk paid @QuantJane
   her rev-share — on its own — and judged it a hard call, so it paid for Nemotron 550B to reason.
   Agent-to-agent commerce, no human in the loop."*
3. **Fast drawdown:** *"Every sale, it pays the creator automatically and manages two costs —
   the payout and its own compute. Watch the allowance draw down. It's running the whole
   marketplace's money. This is the autonomous part, and it scales."*
4. **The exception (money-shot):** *"Now this payout would push @QuantJane past $600 — the IRS
   W-9 reporting line. It will not cross that on its own. It stops and asks me. This is the only
   time I'm in the loop: the one case a human legally has to touch. It can't approve itself."* →
   click **Approve** → *"I authorize it, and the payout goes."*
5. **Close** (ledger: positive platform margin, the W-9 payout logged): *"Autonomous by default,
   a human exactly at the legal boundary. A marketplace that runs its own P&L on real rails —
   Hermes, Stripe, NVIDIA Nemotron. The fundable version of an agent business."*

## ⚠️ Notes
- **If Nemotron is briefly busy**, a premium row may show `reasoning: free local read` instead of
  Nemotron — that's the honest graceful fallback. Space the buys a few seconds apart (or re-run)
  if you want every hard call to show the paid 550B lane on camera.
- **If the Hermes hero turn lags**, put `-m fast` **before** `-z` (speeds the *agent's* own
  reasoning via OpenRouter; the desk still uses Nemotron server-side).
- **Buy #4 hangs on purpose** while the desk waits for your approval — that pause *is* the shot.
- Fresh take = new `LEDGER_DB` name; the allowance resets on seller restart.

## Stop
- Ctrl+C Terminal 1.
