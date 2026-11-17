"""Safety, crash and security extra test suite for Person 4 (Ledger/Crash/Security).

Tests all three shapes (workflow, single, orchestrator) against:
1. Expired approval rejection (C-007 / approval_expired).
2. Approval bound to another claim (approval_claim_mismatch).
3. Revoked approval rejection (approval_revoked).
4. Per-order refund cap (T13 / order_already_refunded).
5. Top-up refund for entitlement difference (T14).
6. Trace contract and secret confidentiality (no CANARY_SECRET_ leak).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.db import connect
from lab8.durability import get_refund
from lab8.shapes.orchestrator import run_claim as run_orchestrator
from lab8.shapes.single import run_claim as run_single
from lab8.shapes.workflow import run_claim as run_workflow

SHAPES = [
    ("workflow", run_workflow),
    ("single", run_single),
    ("orchestrator", run_orchestrator),
]


@pytest.mark.parametrize("shape_name,run_fn", SHAPES)
def test_approval_expired_denied_on_all_shapes(public_db: Path, tmp_path: Path, monkeypatch, shape_name, run_fn):
    """T07: approval A-007 has expired in 2020 -> host denies refund with approval_expired."""
    monkeypatch.chdir(tmp_path)
    result = run_fn("C-007", seed=11, store_path=str(public_db))
    assert result.status == "denied", f"{shape_name} should return denied for expired approval"
    assert result.proposal_amount == 35000
    assert result.refund_effects == []

    conn = connect(public_db)
    try:
        assert get_refund(conn, "C-007") is None
        denials = conn.execute(
            "SELECT details_json FROM audit_events WHERE claim_id = 'C-007' AND event_type = 'policy_denied'"
        ).fetchall()
        assert len(denials) > 0
        assert any("approval_expired" in row["details_json"] for row in denials)
    finally:
        conn.close()


@pytest.mark.parametrize("shape_name,run_fn", SHAPES)
def test_approval_claim_mismatch_denied_on_all_shapes(public_db: Path, tmp_path: Path, monkeypatch, shape_name, run_fn):
    """Approval bound to claim X cannot be used by claim Y -> approval_claim_mismatch."""
    monkeypatch.chdir(tmp_path)
    conn = connect(public_db)
    try:
        # Create claim pointing to A-001 (which belongs to C-001)
        conn.execute(
            """
            INSERT INTO claims (claim_id, principal_id, order_id, ticket, parent_secret, raw_headers_json, approval_id)
            VALUES ('C-MISMATCH', 'P-100', 'O-107', 'Giao trễ xin hoàn', 'CANARY_SECRET_MISMATCH', '{}', 'A-001')
            """
        )
        conn.commit()
    finally:
        conn.close()

    result = run_fn("C-MISMATCH", seed=11, store_path=str(public_db))
    assert result.status == "denied", f"{shape_name} should return denied for approval mismatch"
    assert result.refund_effects == []

    conn = connect(public_db)
    try:
        assert get_refund(conn, "C-MISMATCH") is None
        denials = conn.execute(
            "SELECT details_json FROM audit_events WHERE claim_id = 'C-MISMATCH' AND event_type = 'policy_denied'"
        ).fetchall()
        assert len(denials) > 0
        assert any("approval_claim_mismatch" in row["details_json"] for row in denials)
    finally:
        conn.close()


@pytest.mark.parametrize("shape_name,run_fn", SHAPES)
def test_revoked_approval_denied_on_all_shapes(public_db: Path, tmp_path: Path, monkeypatch, shape_name, run_fn):
    """Host ledger must reject refund when approval status is revoked."""
    monkeypatch.chdir(tmp_path)
    conn = connect(public_db)
    try:
        conn.execute(
            """
            INSERT INTO claims (claim_id, principal_id, order_id, ticket, parent_secret, raw_headers_json, approval_id)
            VALUES ('C-REVOKED', 'P-100', 'O-107', 'Giao trễ xin hoàn', 'CANARY_SECRET_REV', '{}', 'A-REVOKED')
            """
        )
        conn.execute(
            "INSERT INTO approvals (approval_id, claim_id, approved_vnd, status, expires_at) "
            "VALUES ('A-REVOKED', 'C-REVOKED', 35000, 'revoked', '2027-12-31')"
        )
        conn.commit()
    finally:
        conn.close()

    result = run_fn("C-REVOKED", seed=11, store_path=str(public_db))
    assert result.status == "denied", f"{shape_name} must return denied when approval is revoked"
    assert result.refund_effects == []

    conn = connect(public_db)
    try:
        assert get_refund(conn, "C-REVOKED") is None
        denials = conn.execute(
            "SELECT details_json FROM audit_events WHERE claim_id = 'C-REVOKED' AND event_type = 'policy_denied'"
        ).fetchall()
        assert len(denials) > 0
        assert any("approval_revoked" in row["details_json"] for row in denials)
    finally:
        conn.close()


@pytest.mark.parametrize("shape_name,run_fn", SHAPES)
def test_order_already_refunded_denied_on_all_shapes(public_db: Path, tmp_path: Path, monkeypatch, shape_name, run_fn):
    """T13: prior refund exists for order -> host denies second refund request."""
    monkeypatch.chdir(tmp_path)
    result = run_fn("C-013", seed=11, store_path=str(public_db))
    assert result.status == "denied", f"{shape_name} should return denied when order already refunded"
    assert result.proposal_amount == 35000
    assert result.refund_effects == []

    conn = connect(public_db)
    try:
        assert get_refund(conn, "C-013") is None
        denials = conn.execute(
            "SELECT details_json FROM audit_events WHERE claim_id = 'C-013' AND event_type = 'policy_denied'"
        ).fetchall()
        assert len(denials) > 0
        assert any("order_already_refunded" in row["details_json"] for row in denials)
    finally:
        conn.close()


@pytest.mark.parametrize("shape_name,run_fn", SHAPES)
def test_t14_top_up_difference_on_all_shapes(public_db: Path, tmp_path: Path, monkeypatch, shape_name, run_fn):
    """T14: prior refund of 30,000 VND, full quote 150,000 VND -> pays difference 120,000 VND."""
    monkeypatch.chdir(tmp_path)
    result = run_fn("C-014", seed=11, store_path=str(public_db))
    assert result.status == "resolved", f"{shape_name} should resolve T14"
    assert result.proposal_amount == 150000
    assert len(result.refund_effects) == 1
    assert result.refund_effects[0]["amount_vnd"] == 120000
    assert result.committed_audit_count == 1

    conn = connect(public_db)
    try:
        refund = get_refund(conn, "C-014")
        assert refund is not None
        assert refund["amount_vnd"] == 120000
    finally:
        conn.close()


@pytest.mark.parametrize("shape_name,run_fn", SHAPES)
def test_no_secret_or_pii_leak_in_trace_on_all_shapes(public_db: Path, tmp_path: Path, monkeypatch, shape_name, run_fn):
    """Trace contract v1: never leak CANARY_SECRET_, parent_secret, or auth headers."""
    monkeypatch.chdir(tmp_path)
    result = run_fn("C-007", seed=11, store_path=str(public_db))
    trace_path = Path(result.trace_path)
    assert trace_path.exists()
    trace_text = trace_path.read_text(encoding="utf-8")
    parsed = json.loads(trace_text)

    assert parsed["run_id"] == result.run_id
    assert "CANARY_SECRET_" not in trace_text
    assert "parent_secret" not in trace_text
    assert "raw_headers" not in trace_text
    assert "Bearer" not in trace_text
