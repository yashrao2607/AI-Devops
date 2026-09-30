import pytest
from backend.app.models.analysis_schemas import Finding
from backend.app.services.risk_engine import RiskEngine

def make_finding(fid: str, severity: str, confidence: str = "HIGH", impact: str = "HIGH", status: str = "VALIDATED") -> Finding:
    return Finding(
        id=fid,
        category="CODE",
        severity=severity,
        confidence=confidence,
        impact_level=impact,
        title=f"Sample Finding {fid}",
        summary="Summary description",
        impact="Impact description",
        recommendation="Recommendation description",
        repository_id="test_repo",
        file_path="src/main.py",
        line_start=10,
        evidence="sample evidence text",
        agent="CodeAgent",
        status=status
    )

def test_risk_engine_empty_findings():
    eval_res = RiskEngine.evaluate([])
    assert eval_res.risk_score == 0.0
    assert eval_res.risk_level == "LOW"
    assert len(eval_res.contributors) == 0

def test_risk_engine_exact_severity_weights():
    # 1 Critical: 35 * 1.0 * 1.0 = 35.0
    f_crit = make_finding("F-C1", "CRITICAL")
    res_crit = RiskEngine.evaluate([f_crit])
    assert res_crit.risk_score == 35.0
    assert res_crit.risk_level == "MODERATE"

    # 1 High: 25 * 1.0 * 1.0 = 25.0
    f_high = make_finding("F-H1", "HIGH")
    res_high = RiskEngine.evaluate([f_high])
    assert res_high.risk_score == 25.0
    assert res_high.risk_level == "MODERATE"

    # 1 Medium: 15 * 1.0 * 1.0 = 15.0
    f_med = make_finding("F-M1", "MEDIUM")
    res_med = RiskEngine.evaluate([f_med])
    assert res_med.risk_score == 15.0
    assert res_med.risk_level == "LOW"

    # 1 Low: 7 * 1.0 * 1.0 = 7.0
    f_low = make_finding("F-L1", "LOW")
    res_low = RiskEngine.evaluate([f_low])
    assert res_low.risk_score == 7.0
    assert res_low.risk_level == "LOW"

def test_risk_engine_confidence_multipliers():
    # High confidence (1.0): 25 * 1.0 = 25.0
    f_h = make_finding("F-1", "HIGH", confidence="HIGH")
    assert RiskEngine.calculate_finding_contribution(f_h) == 25.0

    # Medium confidence (0.8): 25 * 0.8 = 20.0
    f_m = make_finding("F-2", "HIGH", confidence="MEDIUM")
    assert RiskEngine.calculate_finding_contribution(f_m) == 20.0

    # Low confidence (0.6): 25 * 0.6 = 15.0
    f_l = make_finding("F-3", "HIGH", confidence="LOW")
    assert RiskEngine.calculate_finding_contribution(f_l) == 15.0

def test_risk_engine_excludes_duplicates_and_rejected():
    f_val = make_finding("F-VAL", "HIGH", status="VALIDATED")
    f_dup = make_finding("F-DUP", "CRITICAL", status="DUPLICATE")
    f_rej = make_finding("F-REJ", "CRITICAL", status="REJECTED")
    f_rev = make_finding("F-REV", "HIGH", status="NEEDS_REVIEW")
    f_dis = make_finding("F-DIS", "HIGH", status="DISMISSED")

    eval_res = RiskEngine.evaluate([f_val, f_dup, f_rej, f_rev, f_dis])
    # Only f_val (25.0) contributes
    assert eval_res.risk_score == 25.0
    assert len(eval_res.contributors) == 1
    assert len(eval_res.excluded_findings) == 4
    excluded_ids = [item["finding_id"] for item in eval_res.excluded_findings]
    assert "F-DUP" in excluded_ids
    assert "F-REJ" in excluded_ids
    assert "F-REV" in excluded_ids
    assert "F-DIS" in excluded_ids

def test_risk_engine_score_capped_at_100():
    # 4 Criticals = 4 * 35 = 140 -> Capped at 100.0
    findings = [make_finding(f"F-C{i}", "CRITICAL") for i in range(4)]
    eval_res = RiskEngine.evaluate(findings)
    assert eval_res.raw_score == 140.0
    assert eval_res.risk_score == 100.0
    assert eval_res.risk_level == "CRITICAL"

def test_risk_engine_deterministic_reproducibility():
    findings = [
        make_finding("F-1", "CRITICAL"),
        make_finding("F-2", "HIGH", confidence="MEDIUM"),
        make_finding("F-3", "LOW")
    ]
    run1 = RiskEngine.evaluate(findings)
    run2 = RiskEngine.evaluate(findings)
    assert run1.risk_score == run2.risk_score
    assert run1.risk_level == run2.risk_level
    assert run1.raw_score == run2.raw_score
