"""Extra checks for shape A (workflow). Runs in the host gate (`python -m pytest -q`)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.db import connect
from lab8.durability import get_refund
from lab8.shapes.workflow import run_claim
from tests.conftest import BY_ID, CLAIMS

SEEDS = [11, 22, 33, 44, 55]


@pytest.mark.parametrize("seed", SEEDS)
def test_ticket_delay_is_ignored_on_every_seed(public_db, tmp_path, monkeypatch, seed):
    # T02: ticket says 5 days late, the order row says 2. Swarm pays on seed 55; workflow never does.
    monkeypatch.chdir(tmp_path)
    result = run_claim("C-002", seed=seed, store_path=str(public_db))
    assert result.status == "denied"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    conn = connect(public_db)
    try:
        assert get_refund(conn, "C-002") is None
    finally:
        conn.close()


@pytest.mark.parametrize("claim_id", [row["claim_id"] for row in CLAIMS])
def test_trace_has_no_secret_or_ticket_text(public_db, tmp_path, monkeypatch, claim_id):
    monkeypatch.chdir(tmp_path)
    result = run_claim(claim_id, seed=55, store_path=str(public_db))
    body = Path(result.trace_path).read_text(encoding="utf-8")
    trace = json.loads(body)
    assert trace["run_id"] == result.run_id
    assert isinstance(trace["events"], list) and trace["events"]
    assert "CANARY_" not in body
    assert "Bearer" not in body
    # The ticket is user data: the workflow never copies it into the trace.
    ticket = BY_ID[claim_id]["ticket"]
    if ticket:
        assert ticket not in body


def test_unknown_claim_fails_cleanly_with_trace(public_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = run_claim("C-999", seed=11, store_path=str(public_db))
    assert result.status == "failed"
    assert result.proposal_amount == 0
    assert result.error_reason == "unknown_claim"
    assert Path(result.trace_path).is_file()
