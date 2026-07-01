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

PAYOUT (creator rev-share): release a creator's cut via the Stripe Link CLI; the operator
approves in the Link app when a payout would cross the IRS $600 / W-9 reporting line (the
safety money-shot). Production uses a Stripe Connect transfer; test mode models the money
movement with test credentials — no real funds move.

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

# Auto-approve payout allowance (cents): how much the agent may pay out to creators on its
# OWN — no human in the loop — before a payout must be held for review. It escalates ONLY
# when a payout would cross this line. The real-world line is the IRS $600 / W-9 reporting
# threshold; it's scaled small here so the exception fits on camera. Set via
# PAYOUT_BUDGET_CENTS (DATA_BUDGET_CENTS still honored for back-compat).
PAYOUT_BUDGET_CENTS = int(os.environ.get("PAYOUT_BUDGET_CENTS",
                                         os.environ.get("DATA_BUDGET_CENTS", "500")))
DATA_BUDGET_CENTS = PAYOUT_BUDGET_CENTS  # back-compat alias
_budget_remaining = PAYOUT_BUDGET_CENTS


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


def _request_payout_approval(creator: str, amount_cents: int) -> bool:
    """Escalate a payout that crosses the W-9/$600 line to the human gate via Stripe Link
    CLI (test mode).

    `--test` => card 4242…, NO real funds. `spend-request create` returns
    `pending_approval` + an approval URL; we poll `spend-request retrieve` until the
    operator approves — the agent cannot self-approve. True only on approved/completed.
    In dev (STRIPE_SKILLS_DEV=1), no-op.
    """
    if DEV:
        return True
    import subprocess
    timeout = int(os.environ.get("LINK_APPROVAL_TIMEOUT", "330"))
    # Link requires --context >= 100 chars; spell out exactly what's being released.
    context = (
        f"Creator rev-share payout to {creator} for a sold premium trading signal. This "
        f"payout would take {creator} past the IRS $600 / W-9 reporting threshold, so it "
        f"needs operator approval before release. One-time ${amount_cents / 100:.2f} payout, "
        f"no subscription and no recurring billing (test mode — no real funds move)."
    )
    try:
        create = subprocess.run(
            [LINK_CLI, "spend-request", "create", "--test",
             "--merchant-name", f"Creator payout {creator}",
             "--merchant-url", "https://clockoutcapital.com/creators",
             "--context", context, "--amount", str(amount_cents),
             "--line-item", f"name:{creator} rev-share,unit_amount:{amount_cents},quantity:1",
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
            print(f"\n  💳 APPROVE THIS CREATOR PAYOUT — {creator} crosses the $600/W-9 line "
                  f"(${amount_cents / 100:.2f}, TEST mode — no real money):\n"
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


def _pay_creator_autonomously(creator: str, amount_cents: int) -> bool:
    """Release a creator payout from the auto-approve allowance with NO human in the loop.
    (In production this is a Stripe Connect transfer to the creator; in test mode each
    autonomous payout is modeled by charging a fresh single-use test-helper SPT — the same
    money-movement rails, no real funds.)"""
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


def pay_creator(creator: str, amount_cents: int):
    """Release a creator's rev-share payout; escalate ONLY when it crosses the W-9 line.

    Returns (ok: bool, mode: str):
      'autonomous' — paid from the auto-approve allowance, no human involved (default path)
      'approved'   — would cross the W-9/$600 review line, escalated, human approved
      'denied'     — crosses the line, human declined or timed out
      'failed'     — within the allowance but the autonomous payout failed
    """
    global _budget_remaining
    if amount_cents <= _budget_remaining:
        if _pay_creator_autonomously(creator, amount_cents):
            _budget_remaining -= amount_cents
            return True, "autonomous"
        return False, "failed"
    # Crosses the W-9 review line -> the human gate. The ONLY time a person is in the loop.
    if _request_payout_approval(creator, amount_cents):
        return True, "approved"
    return False, "denied"
