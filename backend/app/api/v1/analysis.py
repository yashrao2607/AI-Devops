import re
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from backend.app.models.analysis_schemas import AnalysisRun, AnalysisReport, Finding, AgentExecutionState
from backend.app.agents.analysis_flow import DeploySafeAnalysisFlow, _ACTIVE_ANALYSIS_RUNS, _ACTIVE_REPORTS
from backend.app.services.rag.loader import RepositoryLoader, RepositorySnapshot, RepositoryLoaderError
from backend.app.services.rag.indexer import RepositoryIndexer
from backend.app.services.rag.vector_store import ChromaVectorStore
from backend.app.api.v1.repositories import _ACTIVE_SNAPSHOTS, lookup_snapshot, register_snapshot
from backend.app.core.logging import logger

router = APIRouter()

def resolve_repository_snapshot(identifier: str, branch: Optional[str] = "main") -> RepositorySnapshot:
    """
    Robustly resolves a repository snapshot from any input format:
    1. In-memory snapshot ID, slug, or target URL.
    2. Cached local directory in cloned_repos/ or demo-repos/ or absolute/relative paths.
    3. On-demand auto-clone and auto-index for GitHub URLs (https://github.com/...) or slugs (owner/repo).
    """
    raw = identifier.strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Repository identifier cannot be empty.")

    # 1. Check in-memory and disk cache
    snapshot = lookup_snapshot(raw)
    if snapshot:
        return snapshot

    # 2. Check if it's a GitHub URL or owner/repo format
    is_github_url = raw.startswith("http://") or raw.startswith("https://") or "github.com/" in raw
    is_github_slug = bool(re.match(r"^[a-zA-Z0-9_\-\.]+/[a-zA-Z0-9_\-\.]+$", raw))

    if is_github_url or is_github_slug:
        logger.info("Repository '%s' not cached. Auto-cloning from GitHub...", raw)
        try:
            snapshot = RepositoryLoader.load_github(url=raw, branch=branch)
            register_snapshot(snapshot, target_alias=raw)

            # Auto-index into Chroma for semantic RAG coverage if not yet indexed
            try:
                vs = ChromaVectorStore()
                if vs.count(snapshot.repository_id) == 0:
                    logger.info("Indexing '%s' into Chroma vector store...", snapshot.repository_id)
                    indexer = RepositoryIndexer()
                    indexer.index_repository(snapshot)
            except Exception as idx_err:
                logger.warning("Auto-indexing for %s had non-fatal warning: %s", snapshot.repository_id, str(idx_err))

            return snapshot
        except RepositoryLoaderError as rle:
            raise HTTPException(status_code=400, detail=f"Failed to clone repository: {str(rle)}")
        except Exception as ex:
            logger.error("Error auto-cloning repository %s: %s", raw, str(ex), exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to clone repository '{raw}': {str(ex)}")

    raise HTTPException(
        status_code=404,
        detail=f"Repository '{raw}' not found. Please provide a valid GitHub repository (e.g. 'yashrao2607/web-scrape' or 'https://github.com/...'), or a local folder path."
    )

class RunAnalysisRequest(BaseModel):
    repository_id: str = Field(description="Ingested repository identifier, slug, or GitHub URL")
    branch: Optional[str] = "main"
    options: Optional[dict] = Field(default_factory=dict)

@router.post("/run", response_model=AnalysisReport)
def trigger_analysis(payload: RunAnalysisRequest):
    """
    Triggers the real multi-agent DeploySafe analysis flow on a repository.
    Automatically resolves, clones if needed, and indexes the repository seamlessly.
    Coordinates Code, Dependency, Config, Test, RAG, Security, and Critic agents.
    """
    snapshot = resolve_repository_snapshot(identifier=payload.repository_id, branch=payload.branch)

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
