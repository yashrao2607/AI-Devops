import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from backend.app.models.analysis_schemas import AnalysisRun, AnalysisReport, Finding, AgentExecutionState
from backend.app.agents.analysis_flow import DeploySafeAnalysisFlow, _ACTIVE_ANALYSIS_RUNS, _ACTIVE_REPORTS
from backend.app.services.rag.loader import RepositoryLoader
from backend.app.api.v1.repositories import _ACTIVE_SNAPSHOTS
from backend.app.core.logging import logger

router = APIRouter()

class RunAnalysisRequest(BaseModel):
    repository_id: str = Field(description="Ingested repository identifier")
    branch: Optional[str] = "main"
    options: Optional[dict] = Field(default_factory=dict)

@router.post("/run", response_model=AnalysisReport)
def trigger_analysis(payload: RunAnalysisRequest):
    """
    Triggers the real multi-agent DeploySafe analysis flow on an ingested repository.
    Coordinates Code, Dependency, Config, Test, RAG, Security, and Critic agents.
    """
    snapshot = _ACTIVE_SNAPSHOTS.get(payload.repository_id)
    if not snapshot:
        # Check if local directory exists as fallback
        target_path = payload.repository_id
        if not os.path.isdir(target_path):
            candidate = os.path.join("demo-repos", payload.repository_id)
            if os.path.isdir(candidate):
                target_path = candidate

        if os.path.isdir(target_path):
            snapshot = RepositoryLoader.load_local(target_path, repository_id=payload.repository_id)
            _ACTIVE_SNAPSHOTS[snapshot.repository_id] = snapshot
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Repository '{payload.repository_id}' not found. Please ingest repository first via /api/v1/repositories/ingest."
            )

    flow = DeploySafeAnalysisFlow()
    try:
        report = flow.execute_flow(snapshot=snapshot, options=payload.options)
        return report
    except Exception as e:
        logger.error("Analysis execution failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis execution failed: {str(e)}")

@router.get("/latest/report", response_model=Optional[AnalysisReport])
def get_latest_report():
    """Returns the most recent analysis report across all sessions, or None."""
    if not _ACTIVE_REPORTS:
        return None
    latest_id = list(_ACTIVE_REPORTS.keys())[-1]
    return _ACTIVE_REPORTS[latest_id]

@router.get("/{run_id}", response_model=AnalysisRun)
def get_analysis_run(run_id: str):
    """Returns real-time execution state and telemetry for an analysis run."""
    run = DeploySafeAnalysisFlow.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Analysis run '{run_id}' not found.")
    return run

@router.get("/{run_id}/report", response_model=AnalysisReport)
def get_analysis_report(run_id: str):
    """Returns the finalized structured analysis report."""
    report = DeploySafeAnalysisFlow.get_report(run_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report for run '{run_id}' not found.")
    return report

@router.get("/{run_id}/findings", response_model=List[Finding])
def get_analysis_findings(
    run_id: str,
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"),
    status: Optional[str] = Query(None, description="Filter by status (VALIDATED, NEEDS_REVIEW, REJECTED)")
):
    """Returns structured findings for an analysis run with optional filtering."""
    report = DeploySafeAnalysisFlow.get_report(run_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Findings for run '{run_id}' not found.")

    findings = report.findings
    if severity:
        findings = [f for f in findings if f.severity.upper() == severity.upper()]
    if status:
        findings = [f for f in findings if f.status.upper() == status.upper()]
    return findings

@router.get("/{run_id}/agents", response_model=List[AgentExecutionState])
def get_analysis_agents(run_id: str):
    """Returns live agent activity and duration metrics."""
    run = DeploySafeAnalysisFlow.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return list(run.agent_states.values())
