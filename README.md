# The Signal Desk — an autonomous agent business

> Built for the **Hermes Agent Accelerated Business Hackathon** (NVIDIA × Stripe × Nous Research).
> An AI agent that **earns, spends, and runs its own P&L** — autonomously — with a human authorizing only
> the boundary, not every transaction.

A self-funding trading-signal API. Buyer agents pay per call (earn). To serve a *premium* signal the desk
buys fresh market data — and it does that **autonomously, within a budget a human authorized once**. Only a
purchase that would **exceed** the budget escalates to a human. Autonomy by default; human authorization at
the edge. It's the *fundable* version of an agent business — the same `propose → approve → execute` pattern
that runs in production at [Clock Out Capital](https://clockoutcapital.com).

---

## How the money flows

```
  Buyer agent ──GET /signal/NVDA──▶  Signal Desk (FastAPI, HTTP-402 seller)
       │                                   │
       │  402 + Stripe payment challenge   │   EARN: charge the buyer's Shared
       │◀──────────────────────────────────│         Payment Token (PaymentIntent)
       │  retry with SPT ──────────────────▶│         ── ledger +$
       │                                   │
       │            premium?               ▼
       │                     ┌─ within budget ──▶ buy data AUTONOMOUSLY (mint+charge SPT)
       │                     │                     ── budget −$0.50, ledger "auto-spend"   (no human)
       │                     └─ over budget  ──▶ escalate → human approves in Stripe Link
       │                                           ── ledger "approved"                    (the exception)
       ▼
   signal + NVIDIA Nemotron 3 Ultra rationale     Live ledger: earn − spend = margin, budget drawing down
```

## Sponsor tech
- **Hermes (Nous Research)** — a Hermes agent is the **buyer**. In oneshot mode (`hermes -z`) with an isolated
  `HERMES_HOME` and a custom `signal-desk-buyer` skill, it reasons on Nemotron, discovers the skill, and pays
  the desk's HTTP-402 — genuine agent-to-agent commerce, no human in the loop.
- **Stripe Skills for Hermes / Shared Payment Tokens** — the buyer pays the 402 with an SPT (earn); the desk
  autonomously mints + charges SPTs to buy data within budget (spend); `@stripe/link-cli --test` drives the
  human approval for the over-budget exception. All **test mode** — no real money moves.
- **NVIDIA Nemotron 3 Ultra** — writes the analyst rationale on every premium signal (OpenAI-compatible API).
- **NVIDIA NemoClaw / OpenShell** — the productized form of this exact `propose → approve → execute` gate;
  cited as the deployment target for the safety layer.
- **Local models** — Clock Out Capital's local Qwen handles the cheap, high-volume lane; Nemotron is the
  frontier "hard-call" lane.

## The autonomy model (why a human is *not* in every loop)
A human authorizes a **budget** (`DATA_BUDGET_CENTS`). The agent then operates inside it on its own —
earning, buying data, managing margin — with no per-transaction approval. The gate fires **only** when a
purchase would exceed what was authorized. That's autonomy that's safe to actually fund: no runaway spend,
no prompt-injection blank check, but no babysitter either.

## Quickstart (test mode)

```bash
# 1. deps (Python only — the earn/spend core needs no npm)
python3 -m venv .venv && .venv/bin/pip install -r seller/requirements.txt

# 2. configure — copy and fill with TEST keys (sk_test_…, nvapi-…)
cp seller/.env.example seller/.env     # then edit

# 3. prove the Stripe + Nemotron lanes work
.venv/bin/python verify_stripe.py      # mints + charges a test SPT  → "EARN LOOP PROVEN"
.venv/bin/python verify_nemotron.py    # one Nemotron 3 Ultra call

# 4. run the desk (loopback) with a small budget for a clean demo
DATA_BUDGET_CENTS=150 .venv/bin/python run_seller.py    # http://127.0.0.1:8800/

# 5. in another terminal, be the buyer
.venv/bin/python buyer_http.py NVDA              # earn
.venv/bin/python buyer_http.py NVDA --premium    # autonomous data spend (×3 within budget)
.venv/bin/python buyer_http.py NVDA --premium    # 4th → exceeds budget → human approves in Stripe Link
```

Open **http://127.0.0.1:8800/** for the live ledger (earn / spend / margin / auto-budget).

## Repo layout
```
seller/
  app.py          FastAPI HTTP-402 seller + live ledger dashboard
  payments.py     Stripe SPT earn-charge + autonomous-budget spend + link-cli escalation
  stripe_http.py  tiny stdlib Stripe client (no SDK dependency)
  reason.py       Nemotron 3 Ultra rationale
  signals.py      signal source (Clock Out Capital screener + offline fallback)
  ledger.py       sqlite earn/spend ledger
run_seller.py     launch the desk (loopback)
buyer_http.py     a buyer agent that pays the 402
agent_buy.py      one-line buyer the Hermes skill invokes (pure stdlib)
hermes/           Hermes agent buyer — config + signal-desk-buyer skill (see hermes/README.md)
verify_stripe.py  / verify_nemotron.py / verify_budget.py   — lane probes
DEMO.md / RECORD.md   video script + recording runbook
```

## Safety & scope
Everything is **test mode**: `sk_test_` keys, Stripe test card `4242…`, `--test` spend credentials. No real
funds move. Money-touching actions are gated by the budget policy and, at the boundary, a human approval the
agent cannot self-grant.

---

*Built on Clock Out Capital's real signal engine and its production `propose → approve → execute` governance.*
