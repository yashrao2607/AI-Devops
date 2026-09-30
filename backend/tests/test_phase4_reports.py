import pytest
from datetime import datetime
from backend.app.models.analysis_schemas import AnalysisReport, Finding
from backend.app.services.report_service import ReportService

@pytest.fixture
def sample_report():
    f1 = Finding(
        id="F-101",
        category="CODE",
        severity="HIGH",
        confidence="HIGH",
        impact_level="HIGH",
        title="Hardcoded Localhost Endpoint",
        summary="Application uses localhost:8080",
        impact="Fails in production container",
        recommendation="Use PAYMENT_GATEWAY_URL env var",
        repository_id="test_repo",
        file_path="src/payment.py",
        line_start=9,
        line_end=9,
        evidence="GATEWAY_URL = 'http://localhost:8080'",
        agent="CodeAgent",
        status="VALIDATED",
        score_contribution=25.0
    )
    return AnalysisReport(
        run_id="run_test123",
        repository_id="test_repo",
        repository_name="test_repo",
        risk_score=25.0,
        risk_level="MODERATE",
        status="COMPLETED",
        analyzed_at=datetime.utcnow(),
        duration_seconds=1.5,
        agents_executed=["code_analysis", "critic", "report"],
        tools_used=["get_file_content"],
        findings=[f1],
        validated_findings=[f1],
        finding_counts_by_severity={"CRITICAL": 0, "HIGH": 1, "MEDIUM": 0, "LOW": 0},
        summary="Found 1 deployment risk.",
        recommendations=["Use PAYMENT_GATEWAY_URL env var"]
    )

def test_generate_markdown_report(sample_report):
    md = ReportService.generate_markdown(sample_report)
    assert "# DeploySafe Deployment Readiness Report" in md
    assert "25.0 / 100" in md
    assert "MODERATE" in md
    assert "src/payment.py:L9" in md
    assert "GATEWAY_URL" in md

def test_generate_html_report(sample_report):
    html = ReportService.generate_html(sample_report)
    assert "<!DOCTYPE html>" in html
    assert "DeploySafe Report - test_repo" in html
    assert "25.0" in html
    assert "src/payment.py:L9" in html
    assert "PAYMENT_GATEWAY_URL" in html

def test_generate_json_report(sample_report):
    json_str = ReportService.generate_json(sample_report)
    assert "run_test123" in json_str
    assert "risk_score" in json_str
