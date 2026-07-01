"""Signal Desk — HTTP-402 seller (the EARN side) + autonomous-budget spend.

A buyer agent requests a trading signal. Unpaid -> 402 Stripe challenge; on retry
with a Shared Payment Token we charge it (earn). A *premium* signal is a creator's
strategy — the desk PAYS THE CREATOR their rev-share AUTONOMOUSLY, and on a hard call
it also pays for its own NVIDIA Nemotron 550B reasoning. Only a payout that would cross
the IRS $600 / W-9 line escalates to a human. The ledger shows earn − payouts − compute
= platform margin, with the auto-payout allowance drawing down.

Run isolated from the production hermes container:
    .venv/bin/python run_seller.py     (loopback 127.0.0.1:8800)
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

import ledger
import payments
import reason
import signals

app = FastAPI(title="Signal Desk", version="0.2.0")

# Pricing (cents). A buyer pays SIGNAL_PRICE; a premium (creator) signal adds the surcharge.
# The platform then covers two costs of its own: the creator's rev-share (CREATOR_PAYOUT) and,
# on hard calls only, its own AI compute (NEMOTRON_COST). Platform margin = earn − both.
SIGNAL_PRICE = 50          # $0.50 / signal (what the buyer pays)
PREMIUM_SURCHARGE = 150    # +$1.50 for a premium (creator strategy + Nemotron) signal
CREATOR_PAYOUT = 50        # creator's rev-share per premium sale — illustrative $ (actual per
                           # Creator Agreement); $0.50 = Stripe's min charge; an autonomous payout
NEMOTRON_COST = 5          # $0.05 — cost of a paid NVIDIA Nemotron 550B "think harder" call

# Fictional demo creators (no real endorsement — surfacing is algorithmic + labeled).
DEMO_CREATORS = ["@QuantJane", "@AlgoAtlas", "@DeltaDidi"]


def _creator_for(ticker: str) -> str:
    return DEMO_CREATORS[sum(ord(c) for c in ticker) % len(DEMO_CREATORS)]


def _is_hard_call(sig: dict) -> bool:
    """Low-conviction / ambiguous setups are the 'hard calls' worth paying to think harder on."""
    score = sig.get("score") or 0
    grade = (sig.get("grade") or "")
    return score < 70 or grade[:1] in ("C", "D", "F")


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "signal-desk"}


@app.get("/ledger")
def get_ledger() -> dict:
    """Live earn/spend tally + autonomous-budget state — powers the money-shot view."""
    s = ledger.summary()
    s["budget_remaining_cents"] = payments.budget_remaining()
    s["budget_total_cents"] = payments.DATA_BUDGET_CENTS
    return s


@app.get("/signal/{ticker}")
async def get_signal(ticker: str, request: Request, premium: bool = False):
    ticker = ticker.upper()
    price = SIGNAL_PRICE + (PREMIUM_SURCHARGE if premium else 0)
    creator = _creator_for(ticker) if premium else None

    # 1) Payment gate. Charges the buyer's incoming SPT; unpaid -> 402 challenge.
    charge = payments.verify_and_charge(request, amount_cents=price, memo=f"signal:{ticker}")
    if not charge.paid:
        return JSONResponse(status_code=402, content=charge.challenge_body,
                            headers=charge.challenge_headers)

    # EARN: the buyer paid; the platform collected revenue.
    earn_memo = f"signal:{ticker}" + (f" premium (via {creator})" if premium else "")
    ledger.record("earn", price, memo=earn_memo)

    body = signals.get_signal(ticker, premium=premium)
    body["paid_cents"] = price

    if premium:
        body["creator"] = creator
        # 2a) PAY THE CREATOR their rev-share AUTONOMOUSLY from the auto-approve allowance;
        #     a payout that would cross the IRS $600 / W-9 line is the ONLY human gate.
        ok, mode = payments.pay_creator(creator, amount_cents=CREATOR_PAYOUT)
        if ok:
            tag = "auto" if mode == "autonomous" else "W-9 review · approved"
            ledger.record("spend", CREATOR_PAYOUT, memo=f"creator-payout:{creator} ({tag})")
        body["spend_mode"] = mode
        body["creator_payout_cents"] = CREATOR_PAYOUT if ok else 0
        body["payout_remaining_cents"] = payments.budget_remaining()
        body["budget_remaining_cents"] = payments.budget_remaining()  # buyer-script compat

        # 2b) PAY FOR ITS OWN INTELLIGENCE: a hard call is worth deep reasoning, so the desk
        #     spends on the NVIDIA Nemotron 550B lane; easy calls use the free built-in read.
        if _is_hard_call(body.get("signal", {})):
            note = reason.rationale(body)                 # paid deep reasoning (Nemotron 550B)
            if note:
                body["reasoning_tier"] = "nemotron-550b"
                body["rationale"] = note
                ledger.record("spend", NEMOTRON_COST,
                              memo=f"compute:Nemotron-550B ({ticker} hard call)")
            else:                                         # Nemotron unavailable -> free fallback
                body["reasoning_tier"] = "local-free"
                body["rationale"] = ""
        else:
            body["reasoning_tier"] = "local-free"         # easy call -> no paid inference
            body["rationale"] = ""

    return body


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    """Tiny live ledger view for the demo."""
    return """<!doctype html><html><head><meta charset="utf-8">
<title>Signal Desk</title><style>
  body{background:#0f1115;color:#e8e8ea;font:15px/1.5 -apple-system,system-ui,sans-serif;margin:0;padding:32px}
  h1{font-size:20px;margin:0 0 4px}.sub{color:#8a8f98;margin-bottom:24px;max-width:780px}
  .cards{display:flex;gap:16px;margin-bottom:24px;flex-wrap:wrap}
  .card{background:#161a22;border:1px solid #232938;border-radius:12px;padding:18px 22px;min-width:150px}
  .card .k{color:#8a8f98;font-size:12px;text-transform:uppercase;letter-spacing:.05em}
  .card .v{font-size:28px;font-weight:700;margin-top:6px}
  .earn{color:#3ddc84}.spend{color:#ff6b1a}.margin{color:#5b9dff}.budget{color:#c9a3ff;font-size:22px}
  table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:8px 10px;border-bottom:1px solid #232938}
  th{color:#8a8f98;font-size:12px;text-transform:uppercase}
  .tag{font-size:11px;padding:2px 8px;border-radius:99px}
  .t-earn{background:#103b25;color:#3ddc84}.t-spend{background:#3b2410;color:#ff6b1a}.t-auto{background:#10303b;color:#5bd1ff}.t-compute{background:#2a2340;color:#c9a3ff}
</style></head><body>
<h1>Signal Desk <span style="color:#ff6b1a">·</span> autonomous creator marketplace</h1>
<div class="sub">Sells creators' premium signals to buyer agents (Stripe Shared Payment Tokens), pays each creator
their rev-share <b>autonomously</b>, and buys its own <b>NVIDIA Nemotron</b> reasoning on the hard calls — a human
approves <b>only</b> a payout that crosses the $600 / W-9 line.</div>
<div class="cards">
  <div class="card"><div class="k">Earned (buyers)</div><div class="v earn" id="earn">$0.00</div></div>
  <div class="card"><div class="k">Paid out (creators + compute)</div><div class="v spend" id="spend">$0.00</div></div>
  <div class="card"><div class="k">Platform margin</div><div class="v margin" id="margin">$0.00</div></div>
  <div class="card"><div class="k">Auto-payout left</div><div class="v budget" id="budget">$0.00</div></div>
</div>
<table><thead><tr><th>When</th><th>Type</th><th>Amount</th><th>Memo</th></tr></thead>
<tbody id="rows"></tbody></table>
<script>
const usd=c=>'$'+(c/100).toFixed(2);
async function tick(){
  const r=await fetch('/ledger');const d=await r.json();
  earn.textContent=usd(d.earn_cents);spend.textContent=usd(d.spend_cents);margin.textContent=usd(d.margin_cents);
  budget.textContent=usd(d.budget_remaining_cents)+' / '+usd(d.budget_total_cents);
  rows.innerHTML=d.recent.map(e=>{
    const compute=e.kind==='spend'&&/^compute:/.test(e.memo);
    const auto=e.kind==='spend'&&/\(auto\)/.test(e.memo);
    const cls=e.kind==='earn'?'t-earn':(compute?'t-compute':(auto?'t-auto':'t-spend'));
    const lbl=e.kind==='earn'?'earn':(compute?'compute':(auto?'auto-payout':'W-9 approved'));
    return `<tr><td>${new Date(e.ts*1000).toLocaleTimeString()}</td>`+
      `<td><span class="tag ${cls}">${lbl}</span></td><td>${usd(e.amount_cents)}</td><td>${e.memo}</td></tr>`;
  }).join('');
}
tick();setInterval(tick,2000);
</script></body></html>"""
