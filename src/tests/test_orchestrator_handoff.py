"""Unit and integration tests for Shape C (orchestrator) and handoff.v1."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from lab8.durability import InjectedCrash
from lab8.handoff import HandoffError, make_handoff
from lab8.shapes.orchestrator import run_claim


def test_orchestrator_trace_contract_and_no_secret_leak(public_db: Path, tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = run_claim("C-010", seed=11, store_path=str(public_db))

    trace_file = Path(result.trace_path)
    assert trace_file.exists()
    payload = json.loads(trace_file.read_text(encoding="utf-8"))
    assert payload["run_id"] == result.run_id
    assert isinstance(payload["events"], list)
    assert len(payload["events"]) > 0

    serialized = json.dumps(payload, ensure_ascii=False) + json.dumps(
        dataclasses.asdict(result), ensure_ascii=False
    )
    assert "CANARY_SECRET_" not in serialized
    assert "parent_secret" not in serialized
    assert "raw_headers" not in serialized


def test_orchestrator_passes_full_quote_for_per_order_cap(public_db: Path, tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = run_claim("C-014", seed=11, store_path=str(public_db))

    assert result.status == "resolved"
    assert result.proposal_amount == 150000
    assert len(result.refund_effects) == 1
    assert result.refund_effects[0]["amount_vnd"] == 120000
    assert result.committed_audit_count == 1


def test_orchestrator_crash_and_resume_idempotent(public_db: Path, tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(InjectedCrash):
        run_claim(
            "C-001",
            seed=11,
            store_path=str(public_db),
            crash_at="after_effect_before_checkpoint",
        )

    resumed = run_claim("C-001", seed=11, store_path=str(public_db), crash_at=None)
    assert resumed.status == "resolved"
    assert len(resumed.refund_effects) == 1
    assert resumed.refund_effects[0]["amount_vnd"] == 35000
    assert resumed.committed_audit_count == 1


def test_handoff_rejects_write_tools_and_drops_extra_facts():
    with pytest.raises(HandoffError):
        make_handoff(
            request_id="REQ-WRITE",
            claim_id="C-001",
            task="refund",
            facts={},
            allowed_tools=["lookup_order", "issue_refund"],
        )

    cleaned = make_handoff(
        request_id="REQ-CLEAN",
        claim_id="C-001",
        task="check_applicable_policy",
        facts={
            "delay_days": 4,
            "parent_secret": "CANARY_SECRET_SHOULD_DROP",
            "phone": "0900000000",
        },
        allowed_tools=["lookup_order", "lookup_policy"],
    )
    assert cleaned["facts"] == {"delay_days": 4}
    assert "CANARY_SECRET_" not in json.dumps(cleaned)
