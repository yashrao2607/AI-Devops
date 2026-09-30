import os
from fastapi import APIRouter, HTTPException, Query
from backend.app.models.schemas import ReadinessAssessmentResult
from backend.app.agents.initial_flow import RepositoryReadinessFlow
from backend.app.core.logging import logger

router = APIRouter()

@router.post("/run-initial", response_model=ReadinessAssessmentResult)
def run_initial_flow(
    repo_path: str = Query(default=None, description="Optional path to local repository to inspect"),
    target_branch: str = Query(default="main", description="Target branch")
):
    """
    Triggers the Phase-1 Readiness Flow.
    Returns structured assessment with findings, risk score, and execution trace.
    """
    target = repo_path or os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    try:
        flow = RepositoryReadinessFlow(repository_path=target)
        result = flow.execute(target_branch=target_branch)
        return result
    except Exception as e:
        logger.error("Flow execution error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Flow execution failed: {str(e)}")
