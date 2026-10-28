import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.analysis_schemas import Finding, AnalysisReport
from backend.app.services.repo_config import RepoConfigService, DeploySafeRepoConfig
from backend.app.services.change_impact import ChangeImpactService
from backend.app.services.patch_service import PatchService
from backend.app.services.history_analytics import HistoryAnalyticsService
from backend.app.services.gate_policy import GatePolicyEngine
from backend.app.agents.analysis_flow import _ACTIVE_REPORTS

client = TestClient(app)

def test_repo_config_security_validation():
    # Test path traversal rejection
    malicious_paths = ["../etc/passwd", "/root/secret", "safe/path.py"]
    cfg = DeploySafeRepoConfig(
        risk_threshold=40.0,
        ignored_paths=malicious_paths,
        required_checks=["code_analysis", "malicious_unapproved_check"]
    )
    assert cfg.risk_threshold == 40.0
    assert "../etc/passwd" not in cfg.ignored_paths
    assert "/root/secret" not in cfg.ignored_paths
    assert "safe/path.py" in cfg.ignored_paths
    assert "code_analysis" in cfg.required_checks
    assert "malicious_unapproved_check" not in cfg.required_checks

def test_repo_config_loading_from_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "deploysafe.yml")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("risk_threshold: 35.0\nblock_on_critical: true\nblock_on_high: true\n")

        loaded = RepoConfigService.load_config(tmpdir)
        assert loaded.risk_threshold == 35.0
        assert loaded.block_on_high is True

        # Test policy integration
        policy = GatePolicyEngine.policy_from_repo_config(loaded)
        assert policy.max_risk_score == 35.0
        assert policy.block_on_critical is True
        assert policy.max_high_count == 1

def test_change_impact_service():
    changed_files = [
        "src/config/env.py",
        "Dockerfile",
        "requirements.txt",
        "tests/test_api.py"
    ]
    report = ChangeImpactService.analyze_impact("test-repo", changed_files)
    assert report.total_changed_files == 4
    assert "CONFIGURATION" in report.impacted_components
    assert "CONTAINERIZATION" in report.impacted_components
    assert "DEPENDENCIES" in report.impacted_components
    assert "TEST_SUITE" in report.impacted_components
    assert report.highest_risk_radius == "HIGH"
    assert len(report.details) == 4

def test_patch_service_generation():
    f = Finding(
        id="F-PATCH-1",
        category="CONFIGURATION",
        severity="HIGH",
        confidence="HIGH",
        title="Missing Stripe API key",
        summary="Missing env var in deployment",
        impact="Payments will fail",
        recommendation="Add STRIPE_API_KEY to .env.example",
        repository_id="repo-patch",
        file_path=".env.example",
        line_start=5,
        line_end=5,
        evidence="PORT=8000\nHOST=0.0.0.0",
        agent="config_analysis",
        status="VALIDATED"
    )
    patch = PatchService.generate_patch_preview(f)
    assert patch.finding_id == "F-PATCH-1"
    assert "--- a/.env.example" in patch.proposed_patch
    assert "+++ b/.env.example" in patch.proposed_patch
    assert "AI-GENERATED PROPOSAL" in patch.disclaimer
    assert "STRIPE_API_KEY" in patch.proposed_patch

def test_history_analytics_service():
    r1 = AnalysisReport(
        run_id="run-h1",
        repository_id="repo-hist",
        repository_name="hist-repo",
        risk_score=60.0,
        risk_level="HIGH",
        findings=[
            Finding(
                id="F-1",
                category="SECURITY",
                severity="HIGH",
                confidence="HIGH",
                title="Secret in token.py",
                summary="Hardcoded secret",
                impact="Leaked credentials",
                recommendation="Remove key",
                repository_id="repo-hist",
                file_path="src/token.py",
                line_start=10,
                evidence="KEY='123'",
                agent="security_analysis",
                status="VALIDATED"
            )
        ],
        summary="Run 1"
    )
    r2 = AnalysisReport(
        run_id="run-h2",
        repository_id="repo-hist",
        repository_name="hist-repo",
        risk_score=25.0,
        risk_level="LOW",
        findings=[],
        summary="Run 2 clean"
    )
    _ACTIVE_REPORTS[r1.run_id] = r1
    _ACTIVE_REPORTS[r2.run_id] = r2

    analytics = HistoryAnalyticsService.analyze_repository_history("repo-hist")
    assert analytics.total_runs_analyzed >= 2
    assert analytics.latest_score == 25.0
    assert analytics.resolution_velocity_pct == 100.0

def test_v2_api_endpoints():
    r = AnalysisReport(
        run_id="run-api-v2",
        repository_id="repo-api-v2",
        repository_name="api-v2-repo",
        risk_score=30.0,
        risk_level="MODERATE",
        findings=[
            Finding(
                id="F-V2-API",
                category="CODE",
                severity="MEDIUM",
                confidence="HIGH",
                title="Unhandled error in service",
                summary="Missing try-catch",
                impact="Crash on null",
                recommendation="Wrap in try/except",
                repository_id="repo-api-v2",
                file_path="src/service.py",
                line_start=15,
                evidence="def run(): crash()",
                agent="code_analysis",
                status="VALIDATED"
            )
        ],
        summary="V2 API run"
    )
    _ACTIVE_REPORTS[r.run_id] = r

    # 1. Test Impact endpoint
    resp1 = client.get(f"/api/v1/runs/{r.run_id}/impact")
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["repository_id"] == "repo-api-v2"
    assert "SOURCE_CODE" in data1["impacted_components"]

    # 2. Test Patch endpoint
    resp2 = client.get("/api/v1/findings/F-V2-API/patch")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["finding_id"] == "F-V2-API"
    assert "AI-GENERATED PROPOSAL" in data2["disclaimer"]

    # 3. Test Analytics endpoint
    resp3 = client.get(f"/api/v1/repositories/{r.repository_id}/analytics")
    assert resp3.status_code == 200
    data3 = resp3.json()
    assert data3["total_runs_analyzed"] >= 1
