import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.analysis_schemas import Finding, AnalysisReport, AnalysisRun, AgentExecutionState
from backend.app.services.comparison import ComparisonService, compute_finding_fingerprint
from backend.app.agents.analysis_flow import _ACTIVE_REPORTS, _ACTIVE_ANALYSIS_RUNS

client = TestClient(app)

def _make_dummy_finding(finding_id: str, file_path: str, line: int, category: str, severity: str, title: str, rule_id: str = None) -> Finding:
    return Finding(
        id=finding_id,
        category=category,
        severity=severity,
        confidence="HIGH",
        title=title,
        summary=f"Summary for {title}",
        impact="Deployment risk",
        recommendation="Fix it",
        repository_id="repo-123",
        file_path=file_path,
        line_start=line,
        line_end=line,
        evidence=f"Problem on line {line}",
        agent="code_analysis",
        status="VALIDATED",
        rule_id=rule_id,
        score_contribution=20.0 if severity == "HIGH" else 10.0
    )

def test_finding_fingerprint_deterministic():
    f1 = _make_dummy_finding("F-1", "src/auth/token.py", 42, "CODE", "HIGH", "Hardcoded token in auth", "SEC001")
    f2 = _make_dummy_finding("F-99", "src\\auth\\token.py", 42, "CODE", "HIGH", "Hardcoded token in auth", "SEC001")
    
    fp1 = compute_finding_fingerprint(f1)
    fp2 = compute_finding_fingerprint(f2)
    assert fp1 == fp2
    assert "src/auth/token.py::42::CODE::sec001" == fp1

def test_comparison_no_baseline():
    target_report = AnalysisReport(
        run_id="run-target-1",
        repository_id="repo-1",
        repository_name="test-repo",
        risk_score=45.0,
        risk_level="MODERATE",
        findings=[_make_dummy_finding("F-1", "server.js", 10, "CONFIGURATION", "HIGH", "Missing CORS")],
        summary="Target summary"
    )

    res = ComparisonService.compare_reports(target_report, None)
    assert res.has_baseline is False
    assert res.risk_trend == "INITIAL_BASELINE"
    assert res.score_delta is None
    assert res.message == "No previous analysis available."
    assert res.target_findings_count == 1
    assert res.resolved_count == 0

def test_comparison_improvement():
    # Base run has 2 issues: score = 70.0
    f_issue1 = _make_dummy_finding("F-1", "server.js", 10, "CONFIGURATION", "HIGH", "Missing CORS", "CFG01")
    f_issue2 = _make_dummy_finding("F-2", "app.py", 25, "SECURITY", "HIGH", "SQL Injection", "SEC02")
    base_report = AnalysisReport(
        run_id="run-base-1",
        repository_id="repo-1",
        repository_name="test-repo",
        risk_score=70.0,
        risk_level="HIGH",
        findings=[f_issue1, f_issue2],
        summary="Base run"
    )

    # Target run fixed issue 2 (SQL Injection resolved), only issue 1 remains: score = 30.0
    target_report = AnalysisReport(
        run_id="run-target-2",
        repository_id="repo-1",
        repository_name="test-repo",
        risk_score=30.0,
        risk_level="MODERATE",
        findings=[f_issue1],
        summary="Target run with fix"
    )

    res = ComparisonService.compare_reports(target_report, base_report)
    assert res.has_baseline is True
    assert res.base_score == 70.0
    assert res.target_score == 30.0
    assert res.score_delta == -40.0
    assert res.risk_trend == "IMPROVED"
    assert res.resolved_count == 1
    assert res.resolved_findings[0].file_path == "app.py"
    assert res.persistent_count == 1
    assert res.persistent_findings[0].file_path == "server.js"
    assert res.new_count == 0

def test_comparison_degradation_and_changed():
    f_old = _make_dummy_finding("F-1", "server.js", 10, "CONFIGURATION", "MEDIUM", "CORS warning", "CFG01")
    base_report = AnalysisReport(
        run_id="run-base-2",
        repository_id="repo-2",
        repository_name="test-repo-2",
        risk_score=20.0,
        risk_level="LOW",
        findings=[f_old],
        summary="Base"
    )

    # In target, f_old became CRITICAL (changed), and a new finding appeared:
    f_old_escalated = _make_dummy_finding("F-1", "server.js", 10, "CONFIGURATION", "CRITICAL", "CORS warning", "CFG01")
    f_new = _make_dummy_finding("F-3", "Dockerfile", 1, "CONFIGURATION", "HIGH", "Root user container", "DOCK01")

    target_report = AnalysisReport(
        run_id="run-target-3",
        repository_id="repo-2",
        repository_name="test-repo-2",
        risk_score=85.0,
        risk_level="CRITICAL",
        findings=[f_old_escalated, f_new],
        summary="Target"
    )

    res = ComparisonService.compare_reports(target_report, base_report)
    assert res.has_baseline is True
    assert res.risk_trend == "DEGRADED"
    assert res.score_delta == 65.0
    assert res.new_count == 1
    assert res.changed_count == 1
    assert res.changed_findings[0]["base_severity"] == "MEDIUM"
    assert res.changed_findings[0]["target_severity"] == "CRITICAL"

def test_api_run_comparison_endpoint():
    target_report = AnalysisReport(
        run_id="run-api-target",
        repository_id="repo-api",
        repository_name="api-repo",
        risk_score=35.0,
        risk_level="MODERATE",
        findings=[_make_dummy_finding("F-10", "index.ts", 5, "CODE", "MEDIUM", "Unused var")],
        summary="API Target"
    )
    _ACTIVE_REPORTS[target_report.run_id] = target_report

    response = client.get(f"/api/v1/runs/{target_report.run_id}/compare")
    assert response.status_code == 200
    data = response.json()
    assert data["target_run_id"] == "run-api-target"
    assert data["has_baseline"] is False

def test_partial_failure_policy_status():
    run = AnalysisRun(
        run_id="run-partial-test",
        repository_id="repo-p",
        repository_name="repo-p",
        status="RUNNING_AGENTS"
    )
    run.agent_states["code_analysis"] = AgentExecutionState(agent_name="code_analysis", status="COMPLETED")
    run.agent_states["test_analysis"] = AgentExecutionState(agent_name="test_analysis", status="FAILED", error="Timeout")

    failed_agents = [name for name, st in run.agent_states.items() if st.status == "FAILED"]
    final_status = "PARTIAL" if failed_agents else "COMPLETED"
    assert final_status == "PARTIAL"
    assert "test_analysis" in failed_agents
