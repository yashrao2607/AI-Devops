import os
import json
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.observability import (
    ObservabilityService,
    AgentTraceRecord,
    ToolTraceRecord,
    RunTrace
)
from backend.app.services.evaluator import EvaluationEngine, EvaluationSummary


@pytest.fixture
def client():
    return TestClient(app)


# ------------------------------------------------------------------------------
# Observability Service Tests
# ------------------------------------------------------------------------------
def test_observability_trace_lifecycle():
    run_id = "test_run_obs_123"
    trace = ObservabilityService.start_trace(
        run_id=run_id,
        repository_name="demo_repo",
        commit_sha="abc12345",
        pr_number=7
    )
    assert trace.run_id == run_id
    assert trace.status == "PREPARING"
    assert len(trace.events) >= 1

    # Record agent trace
    ObservabilityService.record_agent_trace(
        run_id,
        AgentTraceRecord(
            agent_name="code_analysis",
            role="CodeAnalysisAgent",
            status="COMPLETED",
            start_time="2026-10-28T12:00:00",
            end_time="2026-10-28T12:00:01",
            duration_ms=1200.0,
            tool_calls_count=2,
            findings_count=1
        )
    )

    # Record tool trace
    ObservabilityService.record_tool_trace(
        run_id,
        ToolTraceRecord(
            tool_name="get_file_content",
            agent_name="code_analysis",
            status="SUCCESS",
            duration_ms=45.0,
            input_summary="Read main.py",
            output_summary="Returned 50 lines"
        )
    )

    # Complete trace
    ObservabilityService.complete_trace(
        run_id=run_id,
        status="COMPLETED",
        risk_score=35.0,
        risk_level="MODERATE",
        provider="gemini",
        model="gemini-2.5-flash",
        rag_chunks_retrieved=12
    )

    retrieved = ObservabilityService.get_trace(run_id)
    assert retrieved is not None
    assert retrieved.status == "COMPLETED"
    assert retrieved.risk_score == 35.0
    assert len(retrieved.agent_traces) == 1
    assert len(retrieved.tool_traces) == 1
    assert retrieved.rag_chunks_retrieved == 12


def test_observability_api_endpoints(client):
    run_id = "test_run_obs_api"
    ObservabilityService.start_trace(run_id=run_id, repository_name="test_repo")
    ObservabilityService.complete_trace(
        run_id=run_id,
        status="COMPLETED",
        risk_score=50.0,
        risk_level="HIGH",
        provider="groq",
        model="openai/gpt-oss-120b"
    )

    # Get trace
    resp = client.get(f"/api/v1/runs/{run_id}/trace")
    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] == run_id
    assert data["risk_score"] == 50.0

    # Get timeline
    t_resp = client.get(f"/api/v1/runs/{run_id}/timeline")
    assert t_resp.status_code == 200
    assert len(t_resp.json()) >= 1

    # Get telemetry
    tel_resp = client.get("/api/v1/observability/telemetry")
    assert tel_resp.status_code == 200
    assert "telemetry_events" in tel_resp.json()


# ------------------------------------------------------------------------------
# Evaluation Benchmark Suite Tests
# ------------------------------------------------------------------------------
def test_evaluation_engine_loads_cases():
    cases = EvaluationEngine.load_cases()
    assert len(cases) == 5
    case_ids = [c["case_id"] for c in cases]
    assert "EVAL-01" in case_ids
    assert "EVAL-05" in case_ids


def test_evaluation_clean_baseline_case():
    cases = EvaluationEngine.load_cases()
    clean_case = next(c for c in cases if c["case_id"] == "EVAL-05")
    res = EvaluationEngine.evaluate_case(clean_case)

    assert res.case_id == "EVAL-05"
    assert res.is_clean is True
    assert res.status == "PASS"
    assert res.false_positives == 0


def test_evaluation_secret_leak_case():
    cases = EvaluationEngine.load_cases()
    secret_case = next(c for c in cases if c["case_id"] == "EVAL-02")
    res = EvaluationEngine.evaluate_case(secret_case)

    assert res.case_id == "EVAL-02"
    assert res.is_clean is False
    assert res.status == "PASS"
    assert res.true_positives == 1
    assert res.detected_findings_count >= 1


def test_evaluation_api_endpoints(client):
    cases_resp = client.get("/api/v1/evaluation/cases")
    assert cases_resp.status_code == 200
    assert cases_resp.json()["total_cases"] == 5
