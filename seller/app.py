"""Signal Desk — HTTP-402 seller (the EARN side) + autonomous-budget spend.

A buyer agent requests a trading signal. Unpaid -> 402 Stripe challenge; on retry
with a Shared Payment Token we charge it (earn). A *premium* signal makes the desk
BUY fresh data — it spends AUTONOMOUSLY from a human-authorized budget, and only a
purchase that would exceed the budget escalates to a human approval. Nemotron 3 Ultra
writes the rationale. The ledger shows earn − spend = margin + the budget drawing down.

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

# Pricing (cents). A signal costs the buyer SIGNAL_PRICE; a premium one adds the
# surcharge and costs us DATA_COST to fulfill. Margin = price - cost.
SIGNAL_PRICE = 50          # $0.50 / signal
PREMIUM_SURCHARGE = 150    # +$1.50 for a premium (fresh-data + Nemotron) signal
DATA_COST = 50             # $0.50 per data pull (Stripe's min charge); an autonomous draw


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

    # 1) Payment gate. Charges an incoming SPT; unpaid -> 402 challenge.
    charge = payments.verify_and_charge(request, amount_cents=price, memo=f"signal:{ticker}")
    if not charge.paid:
        return JSONResponse(status_code=402, content=charge.challenge_body,
                            headers=charge.challenge_headers)

    # EARN: revenue landed.
    ledger.record("earn", price, memo=f"signal:{ticker}{' premium' if premium else ''}")

    body = signals.get_signal(ticker, premium=premium)
    body["paid_cents"] = price

    # 2) Premium = the desk buys fresh data to fulfil it. It spends AUTONOMOUSLY from
    #    its human-authorized budget; only an over-budget purchase escalates to a human.
    if premium:
        ok, mode = payments.spend_on_data(ticker, amount_cents=DATA_COST)
        if ok:
            tag = "autonomous" if mode == "autonomous" else "human-approved · over budget"
            ledger.record("spend", DATA_COST, memo=f"data-pull:{ticker} ({tag})")
        body["spend_mode"] = mode
        body["budget_remaining_cents"] = payments.budget_remaining()
        body["rationale"] = reason.rationale(body)  # Nemotron 3 Ultra; "" on failure

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
  .t-earn{background:#103b25;color:#3ddc84}.t-spend{background:#3b2410;color:#ff6b1a}.t-auto{background:#10303b;color:#5bd1ff}
</style></head><body>
<h1>Signal Desk <span style="color:#ff6b1a">·</span> autonomous agent business</h1>
<div class="sub">Earns per call (Stripe Shared Payment Tokens). Buys its own data <b>autonomously</b> within a
human-authorized budget — a human approves <b>only</b> an over-budget purchase. Nemotron 3 Ultra does the analysis.</div>
<div class="cards">
  <div class="card"><div class="k">Earned</div><div class="v earn" id="earn">$0.00</div></div>
  <div class="card"><div class="k">Spent</div><div class="v spend" id="spend">$0.00</div></div>
  <div class="card"><div class="k">Margin</div><div class="v margin" id="margin">$0.00</div></div>
  <div class="card"><div class="k">Auto-budget left</div><div class="v budget" id="budget">$0.00</div></div>
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
    const auto=e.kind==='spend'&&/autonomous/.test(e.memo);
    const cls=e.kind==='earn'?'t-earn':(auto?'t-auto':'t-spend');
    const lbl=e.kind==='earn'?'earn':(auto?'auto-spend':'approved');
    return `<tr><td>${new Date(e.ts*1000).toLocaleTimeString()}</td>`+
      `<td><span class="tag ${cls}">${lbl}</span></td><td>${usd(e.amount_cents)}</td><td>${e.memo}</td></tr>`;
  }).join('');
}
tick();setInterval(tick,2000);
</script></body></html>"""
