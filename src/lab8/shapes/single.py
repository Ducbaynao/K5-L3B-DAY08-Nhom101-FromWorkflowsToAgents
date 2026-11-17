"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import json

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        budget = Budget()
        trace = Trace(make_run_id("single", claim_id, seed))
        budget.add_tool(tool_cost())
        claim = get_claim_view(conn, claim_id)
        trace.add("tool", {"name": "get_claim_view", "found": claim["found"]})

        status = "failed"
        proposal = 0
        if not claim["found"]:
            reason = "unknown_claim"
        elif not claim.get("order_id"):
            status = "needs_info"
            reason = "missing_order_id"
        else:
            def decide(observation: dict) -> dict:
                complete(
                    budget,
                    seed=seed,
                    purpose="decide",
                    prompt=json.dumps(observation, ensure_ascii=False),
                )
                last_tool = observation.get("last_tool")
                if last_tool is None:
                    action = {
                        "tool": "lookup_order",
                        "args": {
                            "order_id": claim["order_id"],
                            "principal_id": claim["principal_id"],
                        },
                    }
                elif last_tool == "lookup_order" and observation["last_result"]["visible"]:
                    action = {
                        "tool": "compute_compensation",
                        "args": {"order": observation["last_result"]["order"]},
                    }
                else:
                    action = {"final": {}}
                trace.add("react_step", {"last_tool": last_tool, "action": action.get("tool", "final")})
                return action

            outcome = run_react(
                conn,
                budget,
                observation={
                    "claim": {key: claim[key] for key in ("claim_id", "order_id", "principal_id")},
                },
                decide=decide,
                max_steps=8,
                worker=True,
            )
            if outcome["stopped"] == "step_cap":
                reason = "step_cap"
            elif outcome["observation"]["last_tool"] == "lookup_order":
                status = "escalated"
                reason = outcome["observation"]["last_result"]["reason"]
            else:
                quote = outcome["observation"]["last_result"]
                proposal = int(quote["amount_vnd"])
                trace.add("quote", {"amount_vnd": proposal, "reason": quote["reason"]})
                if proposal <= 0:
                    status = "denied"
                    reason = quote["reason"]
                else:
                    trace.add("host_call", {"name": "issue_refund", "proposal_amount": proposal})
                    # Persist the read trace before the host can inject a crash.
                    trace.write()
                    refund = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
                    trace.add("host_result", {
                        "ok": refund["ok"],
                        "reason": refund["reason"],
                        "conflict": refund["conflict"],
                    })
                    if refund["ok"]:
                        status = "resolved"
                        reason = None
                    elif refund["conflict"]:
                        reason = refund["reason"]
                    else:
                        status = "denied"
                        reason = refund["reason"]

        trace.add("decision", {"status": status, "reason": reason})
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=reason,
        )
    finally:
        conn.close()
