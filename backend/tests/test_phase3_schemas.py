import pytest
from backend.app.models.analysis_schemas import (
    Evidence,
    Finding,
    CriticResult,
    AnalysisContext,
    AnalysisPlan,
    AnalysisRun,
    AnalysisReport
)

def test_evidence_model_validation():
    ev = Evidence(
        evidence_type="SOURCE_CODE",
        file_path="src/payment.py",
        line_start=8,
        line_end=8,
        snippet="self.gateway_url = 'http://localhost:8080/v1/charge'",
        source="code_analysis",
        repository_id="demo_repo"
    )
    assert ev.file_path == "src/payment.py"
    assert ev.line_start == 8
    assert "localhost" in ev.snippet

def test_finding_model_validation():
    f = Finding(
        id="F-101",
        category="CODE",
        severity="HIGH",
        confidence="HIGH",
        title="Hardcoded local endpoint",
        summary="A local URL was hardcoded in production source code.",
        impact="Will fail in cloud containers.",
        recommendation="Use environment variables.",
        repository_id="demo_repo",
        file_path="src/payment.py",
        line_start=8,
        line_end=8,
        evidence="self.gateway_url = 'http://localhost:8080/v1/charge'",
        agent="CodeAgent",
        status="NEW"
    )
    assert f.id == "F-101"
    assert f.severity == "HIGH"
    assert f.status == "NEW"

def test_critic_result_validation():
    c = CriticResult(
        finding_id="F-101",
        decision="VALIDATED",
        confidence="HIGH",
        reason="Evidence directly verified against repository file."
    )
    assert c.decision == "VALIDATED"
    assert c.duplicate_of_id is None

def test_analysis_report_severity_counts():
    f1 = Finding(
        id="F-1", category="SECURITY", severity="CRITICAL", confidence="HIGH",
        title="Key leak", summary="Leak", impact="Severe", recommendation="Fix",
        repository_id="r", file_path="config.py", line_start=1, line_end=1,
        evidence="KEY=123", agent="SecAgent", status="VALIDATED"
    )
    f2 = Finding(
        id="F-2", category="CODE", severity="HIGH", confidence="HIGH",
        title="Local url", summary="Url", impact="High", recommendation="Fix",
        repository_id="r", file_path="app.py", line_start=1, line_end=1,
        evidence="url=loc", agent="CodeAgent", status="VALIDATED"
    )
    rep = AnalysisReport(
        run_id="run_1", repository_id="r", repository_name="Test",
        summary="Summary", findings=[f1, f2], validated_findings=[f1, f2],
        finding_counts_by_severity={"CRITICAL": 1, "HIGH": 1, "MEDIUM": 0, "LOW": 0}
    )
    assert rep.finding_counts_by_severity["CRITICAL"] == 1
    assert rep.finding_counts_by_severity["HIGH"] == 1
