import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_phase4_full_flow_with_risk_engine_and_dashboard(client):
    # 1. Trigger analysis on demo repository
    run_resp = client.post("/api/v1/analysis/run", json={"repository_id": "deploysafe-analysis-demo"})
    assert run_resp.status_code == 200
    report = run_resp.json()
    run_id = report["run_id"]

    # Verify deterministic risk scoring is present and bounded
    assert "risk_score" in report
    assert "risk_level" in report
    assert 0.0 <= report["risk_score"] <= 100.0
    assert report["risk_level"] in ("LOW", "MODERATE", "HIGH", "CRITICAL")
    assert "score_breakdown" in report
    assert "dedup_summary" in report

    # 2. Query Dashboard summary API
    dash_resp = client.get("/api/v1/dashboard/summary")
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert dash_data["total_runs"] >= 1
    assert dash_data["latest_run_id"] == run_id
    assert dash_data["latest_risk_score"] == report["risk_score"]
    assert dash_data["latest_risk_level"] == report["risk_level"]
    assert len(dash_data["recent_runs"]) >= 1

    # 3. Query Runs list API
    runs_resp = client.get("/api/v1/runs")
    assert runs_resp.status_code == 200
    runs_list = runs_resp.json()
    assert any(r["run_id"] == run_id for r in runs_list)

    # 4. Query Run Details API
    run_detail_resp = client.get(f"/api/v1/runs/{run_id}")
    assert run_detail_resp.status_code == 200
    run_detail = run_detail_resp.json()
    assert run_detail["run_id"] == run_id
    assert run_detail["risk_score"] == report["risk_score"]

    # 5. Query Run Summary API
    run_sum_resp = client.get(f"/api/v1/runs/{run_id}/summary")
    assert run_sum_resp.status_code == 200
    run_sum = run_sum_resp.json()
    assert run_sum["risk_score"] == report["risk_score"]
    assert "score_breakdown" in run_sum

    # 6. Query Run Findings API with filters
    findings_resp = client.get(f"/api/v1/runs/{run_id}/findings?severity=CRITICAL")
    assert findings_resp.status_code == 200
    crit_findings = findings_resp.json()
    assert all(f["severity"] == "CRITICAL" for f in crit_findings)

    # 7. Query Multi-Format Exportable Reports
    md_resp = client.get(f"/api/v1/runs/{run_id}/report?format=markdown")
    assert md_resp.status_code == 200
    assert "DeploySafe Deployment Readiness Report" in md_resp.text
    assert str(report["risk_score"]) in md_resp.text

    html_resp = client.get(f"/api/v1/runs/{run_id}/report?format=html")
    assert html_resp.status_code == 200
    assert "<!DOCTYPE html>" in html_resp.text
    assert str(report["risk_score"]) in html_resp.text

    # 8. Query Global Findings API
    all_findings_resp = client.get("/api/v1/findings")
    assert all_findings_resp.status_code == 200
    all_findings = all_findings_resp.json()
    assert len(all_findings) > 0

    first_finding_id = all_findings[0]["id"]
    single_finding_resp = client.get(f"/api/v1/findings/{first_finding_id}")
    assert single_finding_resp.status_code == 200
    assert single_finding_resp.json()["id"] == first_finding_id

    # 9. Test Finding Status Override & Score Recalculation
    patch_resp = client.patch(
        f"/api/v1/findings/{first_finding_id}/status",
        json={"status": "DISMISSED", "reason": "Verified false positive in staging environment."}
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "DISMISSED"

    # 10. Query Repository Summary API
    repo_sum_resp = client.get(f"/api/v1/repositories/{report['repository_id']}/summary")
    assert repo_sum_resp.status_code == 200
    repo_summary = repo_sum_resp.json()
    assert repo_summary["has_analysis"] is True
    assert repo_summary["latest_run_id"] == run_id

