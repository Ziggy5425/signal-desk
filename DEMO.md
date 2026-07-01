# Demo script + submission writeup

**Entry:** *The Signal Desk* — an **autonomous creator marketplace** that earns, pays its
creators, pays for its own AI, and runs its own P&L.
**Built on:** Hermes (Stripe Skills *for Hermes*) · Stripe Shared Payment Tokens · NVIDIA
Nemotron 3 Ultra · on Clock Out Capital's real signal engine + creator program.
**The thesis:** autonomy by default; the agent runs the marketplace's money on its own — earning
from buyers, paying creators, buying its own reasoning on hard calls — and a human is in the loop
**only** for the one thing that legally requires it: a creator payout crossing the IRS $600 / W-9 line.

---

## ~2.5-minute video script (shot list + narration)

Setup on screen: **left = two terminals (SELLER + BUYER), right = the live ledger**
(`http://127.0.0.1:8800/`). Run the seller with a small allowance so the autonomy + the exception
both fit on camera: `PAYOUT_BUDGET_CENTS=150` → three autonomous creator payouts ($0.50 each),
then the 4th crosses the W-9 line.

**0:00–0:20 — Hook.** Ledger at $0, "Auto-payout left $1.50".
> "This is an autonomous business — a creator marketplace. It sells creators' signals, and it runs
> its own money: earning from buyers, paying creators, even paying for its own AI. I set one limit
> and from here it runs itself."

**0:20–1:05 — THE BUYER IS A HERMES AGENT.** Terminal:
`hermes -z "Use the signal-desk-buyer skill to buy a premium NVDA signal."` The agent reasons (on
**NVIDIA Nemotron**), discovers the `signal-desk-buyer` skill, pays the 402 with a **Stripe Shared
Payment Token**, and reports back. On the ledger: earn +$2.00, an **auto-payout** to @QuantJane,
and a **compute** row for Nemotron.
> "My buyer is a real Hermes agent, on NVIDIA Nemotron. It found a skill, paid my API with a Stripe
> token, got @QuantJane's signal. And to serve it, the desk paid @QuantJane her rev-share — on its
> own — and judged it a hard call, so it paid for Nemotron 550B to reason it through. Two agents
> transacting, no human in the loop."

**0:50–1:45 — AUTONOMY (the core).** BUYER: `buyer_http.py NVDA --premium` ×2. Each earns $2.00,
**pays the creator $0.50 autonomously**, and pays a few cents for reasoning — watch "Auto-payout
left" drop $1.50 → $1.00 → $0.50 → $0.00, every payout tagged **auto-payout**.
> "Every sale, it pays the creator automatically and manages two costs — the payout and its own
> compute — keeping the platform's margin. No approval, no me. It's running the whole marketplace's
> money. This is the autonomous part, and it scales."

**1:45–2:25 — THE EXCEPTION (a human exactly at the legal line).** BUYER: `buyer_http.py NVDA
--premium` (4th). Allowance is $0 → the SELLER prints `💳 APPROVE THIS CREATOR PAYOUT — @QuantJane
crosses the $600/W-9 line` → open it → **click Approve** on camera.
> "Now this payout would push @QuantJane past $600 — the IRS W-9 reporting line. It will not cross
> that on its own. It stops and asks me — the one case a human legally has to touch. It can't
> approve itself. I authorize it, and the payout goes."

**2:25–2:45 — Close.** Ledger: positive platform margin, the approved W-9 payout logged.
> "Autonomous by default, a human exactly at the legal boundary. A marketplace that runs its own
> P&L on real rails — Hermes, Stripe, NVIDIA Nemotron. That's the propose→approve→execute pattern
> I run in production at Clock Out Capital — the *fundable* version of an agent business."

---

## Submission writeup (X post + Typeform)

> 🟢 **The Signal Desk** — an **autonomous creator marketplace**. It earns, pays its creators, pays
> for its own AI, and runs its own P&L. I just set one limit.
>
> Built for the @NousResearch × @nvidia × @stripe autonomous-business hackathon:
> → A **Hermes agent** (on **NVIDIA Nemotron**) is the buyer — it finds a skill and pays the API
> with a Stripe **Shared Payment Token** (earn)
> → The desk pays each creator their rev-share **autonomously**, and buys **Nemotron 550B**
> reasoning on the hard calls (spend)
> → It asks me **only** when a payout crosses the **$600 / W-9** line — the exception, not the rule
>
> Net-positive, at scale. Autonomy by default with a human exactly at the legal boundary — the
> propose→approve→execute pattern I run in production at @clockoutcap, now on the agentic-commerce
> rails. The *fundable* version of an agent business.

---

## Sponsor-tech checklist (make each visible)
- [x] **Stripe Skills / Shared Payment Tokens** — buyer pays the 402 (earn); the desk autonomously
      mints + charges SPTs to pay creators (spend); `link-cli --test` drives the human W-9 approval
      for the over-threshold payout.
- [x] **NVIDIA Nemotron 3 Ultra** — the desk *pays for* 550B reasoning on hard calls (a real,
      metered compute cost on the P&L); easy calls use the free local read.
- [~] **NVIDIA NemoClaw / OpenShell** — cited as the productized form of the propose→approve→execute
      gate (k3s footprint too invasive for the prod box; same pattern).
- [x] **Hermes** — a real Hermes agent (oneshot, isolated `HERMES_HOME`) is the buyer: it loads a
      custom `signal-desk-buyer` skill, reasons on Nemotron, and pays the desk's 402.
- [x] **The differentiator** — autonomy across a real two-sided market (buyers + creators) + an
      agent that respects real tax compliance, escalating exactly the $600/W-9 case.

## Submission checklist
- [ ] 1–3 min video on X, tagging **@NousResearch** + the writeup (post from **@mziegler25**)
- [ ] Drop the X link in Discord **#hermes-announcements**
- [ ] Fill the Typeform — X link + Discord post link + repo link
- [ ] Tick the **$250 participation Stripe credit** box + **NVIDIA privacy consent**
- [ ] Cutoff: **1:59 AM Wed (your TZ)** — submit with buffer
