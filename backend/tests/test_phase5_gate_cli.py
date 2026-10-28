import pytest
from backend.app.services.gate_policy import GatePolicyEngine, GatePolicyConfig, GateResult
from backend.app.cli import parse_args


def test_gate_policy_blocked_on_critical():
    policy = GatePolicyConfig(block_on_critical=True, max_risk_score=70.0)
    # Score is low (20), but there is 1 critical finding
    res = GatePolicyEngine.evaluate(risk_score=20.0, finding_counts={"CRITICAL": 1, "HIGH": 0}, policy=policy)

    assert res.allowed is False
    assert res.status == "BLOCKED"
    assert res.exit_code == 1
    assert any("CRITICAL" in r for r in res.reasons)


def test_gate_policy_blocked_on_score():
    policy = GatePolicyConfig(max_risk_score=60.0, block_on_critical=True)
    # Score is 75.0 > 60.0
    res = GatePolicyEngine.evaluate(risk_score=75.0, finding_counts={"CRITICAL": 0, "HIGH": 1}, policy=policy)

    assert res.allowed is False
    assert res.status == "BLOCKED"
    assert res.exit_code == 1
    assert any("exceeds maximum allowable gate threshold" in r for r in res.reasons)


def test_gate_policy_review_required():
    policy = GatePolicyConfig(review_threshold=40.0, max_risk_score=70.0)
    # Score 50 is in review zone [40, 70]
    res = GatePolicyEngine.evaluate(risk_score=50.0, finding_counts={"CRITICAL": 0, "HIGH": 1}, policy=policy)

    assert res.allowed is True
    assert res.status == "REVIEW_REQUIRED"
    assert res.exit_code == 0
    assert any("review zone" in r.lower() for r in res.reasons)


def test_gate_policy_allowed_clean():
    policy = GatePolicyConfig(review_threshold=40.0, max_risk_score=70.0)
    res = GatePolicyEngine.evaluate(risk_score=15.0, finding_counts={"CRITICAL": 0, "HIGH": 0, "LOW": 2}, policy=policy)

    assert res.allowed is True
    assert res.status == "ALLOWED"
    assert res.exit_code == 0
    assert any("safe deployment limits" in r.lower() for r in res.reasons)


def test_gate_policy_blocked_excess_high():
    policy = GatePolicyConfig(max_high_count=2, max_risk_score=80.0)
    # 3 Highs > max 2
    res = GatePolicyEngine.evaluate(risk_score=40.0, finding_counts={"CRITICAL": 0, "HIGH": 3}, policy=policy)

    assert res.allowed is False
    assert res.status == "BLOCKED"
    assert res.exit_code == 1
