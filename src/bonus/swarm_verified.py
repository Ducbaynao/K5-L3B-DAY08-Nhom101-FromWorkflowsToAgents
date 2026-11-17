"""Bonus B3 — swarm + verifier/aggregator written in code.

Same flow as `lab8.shapes.swarm_reference` (peer + parse model calls, read-only
investigators, the seed % 5 == 0 weakness that trusts the ticket delay). The only
addition is `verify_facts` right after the quote and before any decision or write:

- re-read the order through `lookup_order` (structured row, principal-checked);
- compare the facts the quote was built from (`delay_days`, `status`,
  `damage_verified`) with that row;
- on any mismatch, re-quote once from the structured row with
  `compute_compensation` and add a `verifier_override` trace event.

The verifier runs before the `proposal <= 0` branch, not only before the write, so
it also fixes the swarm *under*-paying (ticket understates the delay -> wrongful deny).
Money still comes from `compute_compensation`; the host is still the only writer.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete, parse_delay_days
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import compute_compensation, lookup_order, tool_cost
from lab8.trace import Trace

SHAPE = "swarm_verified"
VERIFIED_FIELDS = ("delay_days", "status", "damage_verified")
MAX_REPAIR_ROUNDS = 1


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def verify_facts(
    conn: sqlite3.Connection,
    budget: Budget,
    *,
    used_order: dict[str, Any],
    order_id: str,
    principal_id: str,
) -> dict[str, Any]:
    """Compare the facts used for the quote with the structured order row.

    Returns {"ok": True} when they agree, otherwise the mismatching fields and the
    structured order to re-quote from. Only field names and their non-PII values
    (int / status / bool) are returned, so the result is safe to trace.
    """
    budget.add_tool(tool_cost())
    view = lookup_order(conn, order_id, principal_id)
    if not view.get("visible"):
        return {"ok": False, "fields": [], "structured": None, "reason": view.get("reason")}
    structured = view["order"]
    mismatches = {
        field: {"used": used_order.get(field), "structured": structured.get(field)}
        for field in VERIFIED_FIELDS
        if used_order.get(field) != structured.get(field)
    }
    return {"ok": not mismatches, "fields": mismatches, "structured": structured, "reason": None}


def _run(conn: sqlite3.Connection, claim_id: str, *, seed: int, crash_at: str | None) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id(SHAPE, claim_id, seed))

    def done(status: str, proposal: int, reason: str | None) -> RunResult:
        return finish(
            conn,
            shape=SHAPE,
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=reason,
        )

    budget.add_tool(tool_cost())
    claim_row = conn.execute(
        "SELECT claim_id, principal_id, order_id, ticket FROM claims WHERE claim_id = ?",
        (claim_id,),
    ).fetchone()
    if claim_row is None:
        trace.add("error", {"reason": "unknown_claim"})
        return done("failed", 0, "unknown_claim")

    # Swarm peers (unchanged): two model calls on the ticket.
    ticket = claim_row["ticket"]
    complete(budget, seed=seed, purpose="peer", prompt=ticket)
    parsed_delay = parse_delay_days(ticket)
    complete(budget, seed=seed, purpose="parse", prompt=ticket)

    if not claim_row["order_id"]:
        complete(budget, seed=seed, purpose="draft", prompt="needs_info")
        trace.add("decision", {"status": "needs_info"})
        return done("needs_info", 0, "missing_order_id")

    handoff = make_handoff(
        request_id=f"REQ-{claim_id}",
        claim_id=claim_id,
        task="check_applicable_policy",
        facts={},
        allowed_tools=["lookup_order", "lookup_policy", "compute_compensation"],
    )
    trace.add("handoff", safe_dump(handoff))
    investigated = run_readonly_investigators(conn, budget, handoff, principal_id=claim_row["principal_id"])
    order_view = investigated["tools"].get("lookup_order", {})
    trace.add("investigator", {"lookup_order": order_view})
    if not order_view.get("visible"):
        complete(budget, seed=seed, purpose="draft", prompt="escalated")
        return done("escalated", 0, order_view.get("reason"))

    order = dict(order_view["order"])
    # Swarm weakness kept on purpose (same rule as the reference): one seed in five
    # trusts the ticket delay over the DB. The verifier below is what we measure.
    if parsed_delay is not None and parsed_delay != int(order["delay_days"]) and seed % 5 == 0:
        order["delay_days"] = parsed_delay
        trace.add("model_override", {"delay_days": parsed_delay})

    quote_payload = investigated["tools"]["compute_compensation"]
    if order["delay_days"] != order_view["order"]["delay_days"]:
        budget.add_tool(tool_cost())
        quote_payload = compute_compensation(conn, order)

    # --- Verifier / aggregator (the B3 addition) ---------------------------------
    check = verify_facts(
        conn,
        budget,
        used_order=order,
        order_id=claim_row["order_id"],
        principal_id=claim_row["principal_id"],
    )
    rounds = 0
    if not check["ok"] and check["structured"] is not None and rounds < MAX_REPAIR_ROUNDS:
        rounds += 1
        budget.add_tool(tool_cost())
        before = int(quote_payload["amount_vnd"])
        quote_payload = compute_compensation(conn, check["structured"])
        trace.add(
            "verifier_override",
            {
                "fields": check["fields"],
                "amount_before": before,
                "amount_after": int(quote_payload["amount_vnd"]),
                "round": rounds,
            },
        )
    else:
        trace.add("verifier", {"ok": check["ok"]})
    # -----------------------------------------------------------------------------

    proposal = int(quote_payload["amount_vnd"])
    trace.add("quote", quote_payload)
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={proposal}")

    if proposal <= 0:
        return done("denied", 0, quote_payload.get("reason"))

    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    if not outcome["ok"]:
        return done("failed" if outcome["conflict"] else "denied", proposal, outcome["reason"])
    return done("resolved", proposal, None)
