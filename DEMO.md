# Demo script + submission writeup

**Entry:** *The Signal Desk* — an **autonomous** agent business that earns, spends, and runs its own P&L.
**Built on:** Hermes (Stripe Skills *for Hermes*) · Stripe Shared Payment Tokens · NVIDIA Nemotron 3 Ultra ·
on Clock Out Capital's real signal engine.
**The thesis:** autonomy by default; a human authorizes a *budget*, the agent operates within it on its own,
and a human is in the loop **only** for the exception — a purchase that would exceed what it was authorized.

---

## ~2.5-minute video script (shot list + narration)

Setup on screen: **left = two terminals (SELLER + BUYER), right = the live ledger** (`http://127.0.0.1:8800/`).
Run the seller with a small budget so the autonomy + the exception both fit on camera:
`DATA_BUDGET_CENTS=150` → three autonomous data pulls ($0.50 each), then the 4th escalates.

**0:00–0:20 — Hook.** Ledger at $0, "Auto-budget left $1.50".
> "This is an autonomous agent business. It earns, it spends, it runs its own P&L. I gave it a budget to
> operate within — and from here, it runs itself."

**0:20–1:00 — THE BUYER IS A HERMES AGENT.** Terminal:
`hermes -z "Use the signal-desk-buyer skill to buy a premium NVDA signal."` The agent reasons (on **NVIDIA
Nemotron**), discovers the `signal-desk-buyer` skill, pays the 402 with a **Stripe Shared Payment Token**, and
reports the signal + analyst note. Ledger ticks up.
> "My buyer is a real Hermes agent, reasoning on NVIDIA Nemotron. I gave it a goal — it found a skill, paid the
> API with a Stripe token, and got the signal. Agent-to-agent commerce, no human in the loop."

**0:50–1:40 — AUTONOMY (the core).** BUYER: `buyer_http.py NVDA --premium` ×3. Each one earns $2.00 **and the
desk autonomously buys $0.50 of data** — watch "Auto-budget left" drop $1.50 → $1.00 → $0.50 → $0.00, every
spend tagged **auto-spend**.
> "Premium means it needs fresh data — so it buys it. On its own. No approval, no me. It's running the whole
> business: earning, spending, managing margin, drawing down the budget I authorized. This is the autonomous
> part — and it scales."

**1:40–2:20 — THE EXCEPTION (human authorization at the boundary).** BUYER: `buyer_http.py NVDA --premium`
(4th). Budget is $0 → the SELLER prints `💳 APPROVE THIS SPEND` → open it → **click Approve** on camera.
> "Now the budget's spent. It will not just keep spending my money — so it stops and asks. This is the *only*
> time I'm in the loop: the exception, not the rule. It can't approve itself. I authorize it — and the money
> moves."

**2:20–2:45 — Close.** Ledger: positive margin, the approved spend logged.
> "Autonomous by default, with a human authorization at the boundary. Net-positive, at scale. That's the
> propose→approve→execute pattern I run in production at Clock Out Capital — the *fundable* version of an
> agent business, now on the agentic-commerce rails. Hermes, Stripe Skills, NVIDIA Nemotron."

---

## Submission writeup (X post + Typeform)

> 🟢 **The Signal Desk** — an **autonomous** agent business. It earns, spends, and runs its own P&L; I just set
> the budget.
>
> Built for the @NousResearch × @nvidia × @stripe autonomous-business hackathon:
> → A **Hermes agent** (reasoning on **NVIDIA Nemotron**) is the buyer — it finds a skill and pays the API
> with a Stripe **Shared Payment Token** (earn)
> → The desk buys its own market data **autonomously**, within a budget I authorized (spend)
> → It asks me **only** when a purchase would exceed the budget — the exception, not the rule
>
> Net-positive, at scale. Autonomy by default with a human authorization at the boundary — the
> propose→approve→execute pattern I run in production at @clockoutcap, now on the agentic-commerce rails. The
> *fundable* version of an agent business.

---

## Sponsor-tech checklist (make each visible)
- [x] **Stripe Skills / Shared Payment Tokens** — buyer pays the 402 (earn); the agent autonomously mints +
      charges SPTs for data within budget (spend); `link-cli --test` approval for the over-budget exception.
- [x] **NVIDIA Nemotron 3 Ultra** — premium signal rationale (OpenAI-compatible lane).
- [~] **NVIDIA NemoClaw / OpenShell** — cited as the productized form of the propose→approve→execute gate
      (k3s footprint too invasive to run on the prod box; same pattern).
- [x] **Hermes** — a real Hermes agent (oneshot, isolated `HERMES_HOME`) is the buyer: it loads a custom
      `signal-desk-buyer` skill, reasons on Nemotron, and pays the desk's 402.
- [x] **The differentiator** — autonomy within a human-authorized budget; gate only on the exception.

## Submission checklist
- [ ] 1–3 min video on X, tagging **@NousResearch** + the writeup
- [ ] Drop the X link in Discord **#hermes-announcements** (pinned thread has the form)
- [ ] Fill the Typeform — X link + Discord post link
- [ ] (optional) GitHub repo link
- [ ] Tick the **$250 participation Stripe credit** box
- [ ] Cutoff: **1:59 AM Wed (your TZ)** — submit with buffer
