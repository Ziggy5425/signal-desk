"""Append-only earn/spend ledger (sqlite) — powers the live money-shot view."""
from __future__ import annotations

import os
import sqlite3
import time

DB = os.environ.get("LEDGER_DB", os.path.join(os.path.dirname(__file__), "ledger.db"))


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB)
    c.execute(
        "CREATE TABLE IF NOT EXISTS entries ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " ts REAL NOT NULL,"
        " kind TEXT NOT NULL,"          # 'earn' | 'spend'
        " amount_cents INTEGER NOT NULL,"
        " memo TEXT)"
    )
    return c


def record(kind: str, amount_cents: int, memo: str = "") -> None:
    assert kind in ("earn", "spend")
    c = _conn()
    with c:
        c.execute("INSERT INTO entries(ts, kind, amount_cents, memo) VALUES(?,?,?,?)",
                  (time.time(), kind, int(amount_cents), memo))
    c.close()


def summary(limit: int = 20) -> dict:
    c = _conn()
    earn = c.execute("SELECT COALESCE(SUM(amount_cents),0) FROM entries WHERE kind='earn'").fetchone()[0]
    spend = c.execute("SELECT COALESCE(SUM(amount_cents),0) FROM entries WHERE kind='spend'").fetchone()[0]
    rows = c.execute(
        "SELECT ts, kind, amount_cents, memo FROM entries ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    c.close()
    return {
        "earn_cents": earn,
        "spend_cents": spend,
        "margin_cents": earn - spend,
        "recent": [{"ts": r[0], "kind": r[1], "amount_cents": r[2], "memo": r[3]} for r in rows],
    }
