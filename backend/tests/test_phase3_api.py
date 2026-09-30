import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_analysis_run_and_query_api_endpoints(client):
    # 1. Trigger analysis on demo repo
    resp = client.post("/api/v1/analysis/run", json={"repository_id": "deploysafe-analysis-demo"})
    assert resp.status_code == 200
    report = resp.json()
    assert "run_id" in report
    run_id = report["run_id"]
    assert report["status"] == "COMPLETED"
    assert len(report["findings"]) > 0
    assert len(report["validated_findings"]) > 0

    # 2. Query run telemetry
    resp_run = client.get(f"/api/v1/analysis/{run_id}")
    assert resp_run.status_code == 200
    run_data = resp_run.json()
    assert run_data["run_id"] == run_id
    assert run_data["total_findings_count"] == len(report["findings"])

    # 3. Query agents state
    resp_agents = client.get(f"/api/v1/analysis/{run_id}/agents")
    assert resp_agents.status_code == 200
    agents_list = resp_agents.json()
    agent_names = [a["agent_name"] for a in agents_list]
    assert "code_analysis" in agent_names
    assert "dependency_analysis" in agent_names
    assert "configuration_analysis" in agent_names
    assert "test_analysis" in agent_names
    assert "security_analysis" in agent_names
    assert "critic" in agent_names

    # 4. Query report
    resp_rep = client.get(f"/api/v1/analysis/{run_id}/report")
    assert resp_rep.status_code == 200
    rep_data = resp_rep.json()
    assert rep_data["run_id"] == run_id

    # 5. Query findings with filters
    resp_findings = client.get(f"/api/v1/analysis/{run_id}/findings?severity=CRITICAL")
    assert resp_findings.status_code == 200
    crit_findings = resp_findings.json()
    assert all(f["severity"] == "CRITICAL" for f in crit_findings)

    resp_validated = client.get(f"/api/v1/analysis/{run_id}/findings?status=VALIDATED")
    assert resp_validated.status_code == 200
    val_findings = resp_validated.json()
    assert all(f["status"] == "VALIDATED" for f in val_findings)
