"""Checks for Shape B's early exits and bounded read-only ReAct loop."""

import json
import sqlite3
from pathlib import Path

import pytest

from lab8 import runtime
from lab8.db import connect
from lab8.durability import InjectedCrash
from lab8.schemas import make_run_id
from lab8.shapes import single
from lab8.tools import tool_cost


@pytest.mark.parametrize(
    "claim_id, order_id, status, reason",
    [
        ("missing-claim", None, "failed", "unknown_claim"),
        ("C-001", None, "needs_info", "missing_order_id"),
        ("C-001", "", "needs_info", "missing_order_id"),
    ],
)
def test_single_early_exit(public_db, tmp_path, monkeypatch, capsys, claim_id, order_id, status, reason):
    conn = connect(public_db)
    try:
        conn.execute(
            "UPDATE claims SET order_id = ?, ticket = ? WHERE claim_id = ?",
            (order_id, "PRIVATE_TICKET_MUST_STAY_OUT_OF_TRACE", claim_id),
        )
        conn.commit()
        before = conn.execute("SELECT * FROM refund_ledger ORDER BY claim_id").fetchall()
    finally:
        conn.close()


    monkeypatch.chdir(tmp_path)
    run_conn = connect(public_db)
    monkeypatch.setattr(single, "connect", lambda path: run_conn)
    result = single.run_claim(claim_id, seed=11, store_path=str(public_db))

    assert result.status == status
    assert result.error_reason == reason
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    assert result.committed_audit_count == 0
    assert result.tool_calls == 1
    assert result.model_calls == 0
    assert result.cost_estimate == round(tool_cost(), 6)
    assert result.run_id == make_run_id("single", claim_id, 11)
    trace = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
    assert trace["run_id"] == result.run_id
    assert trace["events"] == [
        {"kind": "tool", "payload": {"name": "get_claim_view", "found": claim_id != "missing-claim"}},
        {"kind": "decision", "payload": {"status": status, "reason": reason}},
    ]
    assert capsys.readouterr().out == ""
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        run_conn.execute("SELECT 1")

    conn = connect(public_db)
    try:
        after = conn.execute("SELECT * FROM refund_ledger ORDER BY claim_id").fetchall()
        assert after == before
    finally:
        conn.close()

@pytest.mark.parametrize("claim_id, expected_quote", [("C-001", 35000), ("C-002", 0)])
def test_single_react_reads_order_and_counts_calls(public_db, tmp_path, monkeypatch, capsys, claim_id, expected_quote):
    monkeypatch.chdir(tmp_path)
    dispatched = []
    original_dispatch = runtime.dispatch

    def record_dispatch(conn, budget, name, args, *, worker):
        assert worker is True
        dispatched.append(name)
        return original_dispatch(conn, budget, name, args, worker=worker)

    monkeypatch.setattr(runtime, "dispatch", record_dispatch)
    result = single.run_claim(claim_id, seed=55, store_path=str(public_db))

    assert dispatched == ["lookup_order", "compute_compensation"]
    assert result.proposal_amount == expected_quote
    assert result.model_calls == 3
    assert result.tool_calls == 3
    assert result.input_tokens > 0
    assert result.output_tokens > 0
    assert result.cost_estimate > 3 * tool_cost()
    trace = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
    assert trace["run_id"] == result.run_id
    assert any(event["kind"] == "quote" for event in trace["events"])
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("order_id", ["unknown-order", "O-107"])
def test_single_react_escalates_invisible_order(public_db, tmp_path, monkeypatch, order_id):
    conn = connect(public_db)
    try:
        conn.execute(
            "UPDATE claims SET order_id = ?, principal_id = ? WHERE claim_id = 'C-001'",
            (order_id, "unrelated-principal"),
        )
        conn.commit()
    finally:
        conn.close()
    monkeypatch.chdir(tmp_path)
    result = single.run_claim("C-001", seed=11, store_path=str(public_db))
    assert result.status == "escalated"
    assert result.error_reason in ("not_found", "outside_principal_scope")
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    assert result.model_calls == 2
    assert result.tool_calls == 2


def test_single_step_cap_returns_failed_without_refund(public_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def exhaust_steps(conn, budget, *, observation, decide, max_steps, worker):
        assert max_steps == 8
        assert worker is True
        assert "ticket" not in observation["claim"]

        def repeat_lookup(seen):
            decide(seen)
            return {
                "tool": "lookup_order",
                "args": {
                    "order_id": observation["claim"]["order_id"],
                    "principal_id": observation["claim"]["principal_id"],
                },
            }

        return runtime.run_react(
            conn, budget, observation=observation, decide=repeat_lookup,
            max_steps=max_steps, worker=worker,
        )

    monkeypatch.setattr(single, "run_react", exhaust_steps)
    result = single.run_claim("C-001", seed=11, store_path=str(public_db))
    assert result.status == "failed"
    assert result.error_reason == "step_cap"
    assert result.proposal_amount == 0
    assert result.model_calls == 8
    assert result.tool_calls == 9
    assert result.refund_effects == []
    assert result.committed_audit_count == 0
    trace = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
    assert trace["run_id"] == result.run_id
    assert trace["events"][-1]["payload"]["reason"] == "step_cap"
    conn = connect(public_db)
    try:
        assert conn.execute("SELECT COUNT(*) FROM refund_ledger WHERE claim_id = 'C-001'").fetchone()[0] == 0
    finally:
        conn.close()


@pytest.mark.parametrize("point", ["before_effect", "after_effect_before_checkpoint", "after_checkpoint"])
def test_single_crash_resumes_with_one_refund(public_db, tmp_path, monkeypatch, point):
    monkeypatch.chdir(tmp_path)
    run_conn = connect(public_db)
    with monkeypatch.context() as patch:
        patch.setattr(single, "connect", lambda path: run_conn)
        with pytest.raises(InjectedCrash, match=point):
            single.run_claim("C-001", seed=11, store_path=str(public_db), crash_at=point)
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        run_conn.execute("SELECT 1")
    trace = json.loads(Path("traces/R-single-C-001-s11.json").read_text(encoding="utf-8"))
    assert trace["run_id"] == make_run_id("single", "C-001", 11)
    assert trace["events"][-1]["kind"] == "host_call"

    conn = connect(public_db)
    try:
        count = conn.execute("SELECT COUNT(*) FROM refund_ledger WHERE claim_id = 'C-001'").fetchone()[0]
        assert count == (0 if point == "before_effect" else 1)
    finally:
        conn.close()

    resumed = single.run_claim("C-001", seed=11, store_path=str(public_db))
    replayed = single.run_claim("C-001", seed=11, store_path=str(public_db))
    for result in (resumed, replayed):
        assert result.status == "resolved"
        assert result.proposal_amount == 35000
        assert len(result.refund_effects) == 1
        assert result.refund_effects[0]["amount_vnd"] == 35000
        assert result.committed_audit_count == 1


def test_single_retry_changed_quote_preserves_committed_refund(public_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    first = single.run_claim("C-001", seed=11, store_path=str(public_db))
    assert first.status == "resolved"
    conn = connect(public_db)
    try:
        conn.execute("UPDATE orders SET shipping_fee_vnd = 10000 WHERE order_id = 'O-107'")
        conn.commit()
    finally:
        conn.close()

    result = single.run_claim("C-001", seed=11, store_path=str(public_db))
    assert result.status == "failed"
    assert result.error_reason == "amount_conflict"
    assert result.proposal_amount == 10000
    assert len(result.refund_effects) == 1
    assert result.refund_effects[0]["amount_vnd"] == 35000
    assert result.committed_audit_count == 1

