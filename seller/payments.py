"""Stripe Shared Payment Token (SPT) seam — earn (charge) + spend.

Verified flow (primary: docs.stripe.com/agentic-commerce SPT seller ·
docs.stripe.com/payments/machine/mpp · stripe-samples/machine-payments):

SELLER (earn):
  1. Unpaid request -> HTTP 402 with `WWW-Authenticate: Payment id="chal_..",
     method="stripe", intent="charge"` + RFC-9457 `application/problem+json`.
  2. Buyer retries carrying an SPT (granted_token id `spt_..`). We charge by
     creating a PaymentIntent that references the token (NOT a resolve-then-charge):
        POST /v1/payment_intents
          amount, currency=usd,
          payment_method_data[shared_payment_granted_token]=spt_..,
          confirm=true            (Stripe-Version: 2026-04-22.preview)
     status=succeeded -> release the signal.   (PROVEN live 2026-06-28.)

SPENDER (cost beat): pay a data vendor via the Stripe Link CLI; operator approves
in the Link app (the safety money-shot). npm CLI runs inside the NemoClaw sandbox.

Dev mode (STRIPE_SKILLS_DEV=1): honor a stubbed `X-Payment-Token: test-paid` so the
loop runs without Stripe. Charge path uses raw HTTP (stripe_http) — the proven path.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

DEV = os.environ.get("STRIPE_SKILLS_DEV") == "1"
def _link_cli_bin() -> str:
    env = os.environ.get("LINK_CLI_BIN")
    if env:
        return env
    local = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",
                                          "node_modules", ".bin", "link-cli"))
    return local if os.path.exists(local) else "link-cli"


LINK_CLI = _link_cli_bin()

# Human-authorized AUTONOMOUS data budget (cents). The agent spends within this on its
# own — no human in the loop — and escalates to a human approval ONLY when a purchase
# would exceed what's left. Size it via DATA_BUDGET_CENTS (small => quicker demo).
DATA_BUDGET_CENTS = int(os.environ.get("DATA_BUDGET_CENTS", "500"))
_budget_remaining = DATA_BUDGET_CENTS


@dataclass
class ChargeResult:
    paid: bool
    amount_cents: int = 0
    payment_intent: str | None = None
    challenge_headers: dict = field(default_factory=dict)
    challenge_body: dict = field(default_factory=dict)


def _challenge(amount_cents: int, memo: str) -> ChargeResult:
    """RFC-9457 402 with a Stripe `Payment` challenge.

    The amount/currency/network normally live inside the base64url-encoded
    challenge the `mpp` helper builds; here we surface a readable body for the demo.
    """
    headers = {
        "WWW-Authenticate": 'Payment id="chal_demo", method="stripe", intent="charge"',
        "Content-Type": "application/problem+json",
        "Cache-Control": "no-store",
    }
    body = {
        "type": "https://paymentauth.org/problems/payment-required",
        "title": "Payment Required",
        "status": 402,
        "detail": "Payment is required.",
        "amount_cents": amount_cents,
        "currency": "usd",
        "memo": memo,
        "accept": ["stripe"],
    }
    return ChargeResult(paid=False, challenge_headers=headers, challenge_body=body)


def _extract_spt(request) -> str | None:
    """Pull the SPT id from the buyer's retry. The real `mpp` helper decodes the
    `Authorization: Payment ..` credential; we also accept a plain header."""
    auth = request.headers.get("Authorization", "")
    if "spt_" in auth:
        for tok in auth.replace(",", " ").replace('"', " ").split():
            if tok.startswith("spt_"):
                return tok
    return request.headers.get("X-Shared-Payment-Token")


def verify_and_charge(request, amount_cents: int, memo: str) -> ChargeResult:
    """Charge an incoming SPT via a PaymentIntent. Unpaid -> 402 challenge."""
    if DEV:
        if request.headers.get("X-Payment-Token") == "test-paid":
            return ChargeResult(paid=True, amount_cents=amount_cents, payment_intent="pi_dev")
        return _challenge(amount_cents, memo)

    spt = _extract_spt(request)
    if not spt:
        return _challenge(amount_cents, memo)

    from stripe_http import post
    pi = post("/payment_intents", {
        "amount": amount_cents,
        "currency": "usd",
        "payment_method_data[shared_payment_granted_token]": spt,
        "confirm": "true",
    })
    if pi.get("status") == "succeeded":
        return ChargeResult(paid=True, amount_cents=amount_cents, payment_intent=pi.get("id"))
    return _challenge(amount_cents, memo)


def _last_record(stdout: str) -> dict:
    """link-cli returns a JSON array of state snapshots; take the latest object."""
    import json
    data = json.loads(stdout)
    if isinstance(data, list):
        return data[-1] if data else {}
    return data or {}


def _request_spend_approval(ticker: str, amount_cents: int) -> bool:
    """Escalate an OVER-BUDGET spend to the human gate via Stripe Link CLI (test mode).

    `--test` => card 4242…, NO real funds. `spend-request create` returns
    `pending_approval` + an approval URL; we poll `spend-request retrieve` until the
    operator approves — the agent cannot self-approve. True only on approved/completed.
    In dev (STRIPE_SKILLS_DEV=1), no-op.
    """
    if DEV:
        return True
    import subprocess
    timeout = int(os.environ.get("LINK_APPROVAL_TIMEOUT", "330"))
    # Link requires --context >= 100 chars; spell out exactly what's being bought.
    context = (
        f"Test-mode purchase of one fresh market-data pull for {ticker} to fulfil a paid "
        f"premium trading-signal request. One-time charge of ${amount_cents / 100:.2f}, no "
        f"subscription and no recurring billing. Approve to release the data to the buyer."
    )
    try:
        create = subprocess.run(
            [LINK_CLI, "spend-request", "create", "--test",
             "--merchant-name", "MarketData Feed",
             "--merchant-url", "https://marketdata.example.com",
             "--context", context, "--amount", str(amount_cents),
             "--line-item", f"name:{ticker} data,unit_amount:{amount_cents},quantity:1",
             "--request-approval", "--format", "json"],
            capture_output=True, text=True, timeout=60, check=True)
        rec = _last_record(create.stdout)
        if rec.get("status") in ("approved", "completed"):
            return True
        lsrq = rec.get("id")
        if not lsrq:
            return False
        url = rec.get("approval_url")
        if url:
            import sys
            print(f"\n  💳 APPROVE THIS SPEND (${amount_cents / 100:.2f}, TEST mode — no real money):\n"
                  f"     {url}\n", file=sys.stderr, flush=True)
            try:
                with open(os.path.join(os.path.dirname(__file__), "..", "approval_url.txt"), "w") as fh:
                    fh.write(url + "\n")
            except Exception:
                pass
        poll = subprocess.run(
            [LINK_CLI, "spend-request", "retrieve", lsrq,
             "--interval", "2", "--max-attempts", str(max(1, timeout // 2)),
             "--format", "json"],
            capture_output=True, text=True, timeout=timeout + 20, check=True)
        return _last_record(poll.stdout).get("status") in ("approved", "completed")
    except Exception:
        return False


def budget_remaining() -> int:
    """Cents left in the human-authorized autonomous data budget."""
    return _budget_remaining


def _charge_vendor_autonomously(ticker: str, amount_cents: int) -> bool:
    """Pay the data vendor from the authorized budget with NO human in the loop:
    mint a fresh single-use SPT for exactly this amount and charge it once. (In
    production this would draw on a budgeted mandate / Issuing card; in test mode each
    autonomous draw is a fresh test-helper SPT.)"""
    if DEV:
        return True
    import time
    from stripe_http import post
    try:
        spt = post("/test_helpers/shared_payment/granted_tokens", {
            "payment_method": "pm_card_visa", "usage_limits[currency]": "usd",
            "usage_limits[max_amount]": str(amount_cents),
            "usage_limits[expires_at]": str(int(time.time()) + 600),
        })["id"]
        pi = post("/payment_intents", {
            "amount": str(amount_cents), "currency": "usd",
            "payment_method_data[shared_payment_granted_token]": spt, "confirm": "true",
        })
        return pi.get("status") == "succeeded"
    except Exception:
        return False


def spend_on_data(ticker: str, amount_cents: int):
    """Spend within the human-authorized autonomous budget; escalate ONLY when over.

    Returns (ok: bool, mode: str):
      'autonomous' — paid from the budget, no human involved (the default path)
      'approved'   — exceeded the budget, escalated, human approved (the exception)
      'denied'     — exceeded the budget, human declined or timed out
      'failed'     — within budget but the autonomous charge failed
    """
    global _budget_remaining
    if amount_cents <= _budget_remaining:
        if _charge_vendor_autonomously(ticker, amount_cents):
            _budget_remaining -= amount_cents
            return True, "autonomous"
        return False, "failed"
    # Over budget -> the human gate. The ONLY time a person is in the loop.
    if _request_spend_approval(ticker, amount_cents):
        return True, "approved"
    return False, "denied"
