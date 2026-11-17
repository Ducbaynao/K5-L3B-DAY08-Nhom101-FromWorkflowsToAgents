"""Bonus B3: swarm + code verifier. Runs in the host gate (`python -m pytest -q`)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bonus.swarm_verified import run_claim as verified_run, verify_facts
from lab8.db import connect, init_store, load_json, load_jsonl
from lab8.durability import InjectedCrash, committed_audit_count, get_refund
from lab8.metrics import trial_pass
from lab8.schemas import Budget
from lab8.shapes.swarm_reference import run_claim as swarm_run
from lab8.shapes.workflow import run_claim as workflow_run

BONUS_DIR = Path(__file__).resolve().parents[1] / "bonus"
BONUS_WORLD = load_json(BONUS_DIR / "world.json")
BONUS_CASES = load_jsonl(BONUS_DIR / "cases.jsonl")
BONUS_IDS = [row["claim_id"] for row in BONUS_CASES]
BONUS_BY_ID = {row["claim_id"]: row for row in BONUS_CASES}


@pytest.fixture
def bonus_db(tmp_path: Path) -> Path:
    store = tmp_path / "bonus.sqlite"
    init_store(store, BONUS_WORLD, BONUS_CASES).close()
    return store


def _events(result) -> list[dict]:
    return json.loads(Path(result.trace_path).read_text(encoding="utf-8"))["events"]


def test_verifier_overrides_ticket_delay_on_t02_seed_55(public_db, tmp_path, monkeypatch):
    # Reference swarm pays 20000 on C-002 seed 55; the verifier must restore the DB delay and deny.
    monkeypatch.chdir(tmp_path)
    swarm = swarm_run("C-002", seed=55, store_path=str(public_db))
    assert swarm.status == "resolved"  # the known reference miss

    fresh = tmp_path / "fresh.sqlite"
    from tests.conftest import CLAIMS, WORLD

    init_store(fresh, WORLD, CLAIMS).close()
    result = verified_run("C-002", seed=55, store_path=str(fresh))
    assert result.status == "denied"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    overrides = [e for e in _events(result) if e["kind"] == "verifier_override"]
    assert len(overrides) == 1
    payload = overrides[0]["payload"]
    assert payload["fields"] == {"delay_days": {"used": 5, "structured": 2}}
    assert (payload["amount_before"], payload["amount_after"]) == (20000, 0)


@pytest.mark.parametrize("seed", [11, 22, 33, 44])
def test_verifier_is_silent_when_swarm_trusts_the_db(public_db, tmp_path, monkeypatch, seed):
    # Off the weak seed, swarm_verified must decide exactly like swarm and never override.
    monkeypatch.chdir(tmp_path)
    result = verified_run("C-002", seed=seed, store_path=str(public_db))
    kinds = [e["kind"] for e in _events(result)]
    assert "verifier_override" not in kinds
    assert "verifier" in kinds
    assert result.status == "denied"


@pytest.mark.parametrize(
    "field,used_value",
    [("status", "delivered_late"), ("damage_verified", True), ("delay_days", 9)],
)
def test_verify_facts_catches_every_quoted_field(bonus_db, field, used_value):
    # The benchmark only exercises delay_days (the swarm's weakness); check status and damage directly.
    conn = connect(bonus_db)
    try:
        structured = {"status": "cancelled", "delay_days": 7, "damage_verified": False}
        used = dict(structured, **{field: used_value})
        check = verify_facts(conn, Budget(), used_order=used, order_id="O-B05", principal_id="P-100")
    finally:
        conn.close()
    assert check["ok"] is False
    assert list(check["fields"]) == [field]
    assert check["structured"]["order_id"] == "O-B05"


@pytest.mark.parametrize("claim_id", BONUS_IDS)
def test_hand_labels_hold_for_workflow_and_swarm_verified_on_seed_55(tmp_path, monkeypatch, claim_id):
    # Workflow never reads the ticket, so it cross-checks the hand-written labels;
    # swarm_verified must match them on the seed where the swarm trusts the ticket.
    monkeypatch.chdir(tmp_path)
    expected = BONUS_BY_ID[claim_id]["expected"]
    for name, fn in (("workflow", workflow_run), ("swarm_verified", verified_run)):
        store = tmp_path / f"{name}-{claim_id}.sqlite"
        init_store(store, BONUS_WORLD, BONUS_CASES).close()
        result = fn(claim_id, seed=55, store_path=str(store))
        conn = connect(store)
        try:
            ok, reason = trial_pass(result.as_dict(), expected, conn)
        finally:
            conn.close()
        assert ok, f"{name} {claim_id}: {reason}"


@pytest.mark.parametrize("point", ["before_effect", "after_effect_before_checkpoint", "after_checkpoint"])
def test_swarm_verified_crash_then_resume_keeps_one_refund(bonus_db, tmp_path, monkeypatch, point):
    # B-002: ticket understates the delay; at seed 55 only the verifier makes the quote positive.
    monkeypatch.chdir(tmp_path)
    with pytest.raises(InjectedCrash):
        verified_run("B-002", seed=55, store_path=str(bonus_db), crash_at=point)
    result = verified_run("B-002", seed=55, store_path=str(bonus_db))
    assert result.status == "resolved"
    conn = connect(bonus_db)
    try:
        assert int(get_refund(conn, "B-002")["amount_vnd"]) == 30000
        assert committed_audit_count(conn, "B-002") == 1
    finally:
        conn.close()


def test_verifier_trace_has_no_secret_or_pii(bonus_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for claim_id in BONUS_IDS:
        result = verified_run(claim_id, seed=55, store_path=str(bonus_db))
        body = Path(result.trace_path).read_text(encoding="utf-8")
        assert "CANARY_" not in body
        assert "Bearer" not in body
        assert "Bonus St" not in body and "09010B" not in body  # address / phone of bonus orders
