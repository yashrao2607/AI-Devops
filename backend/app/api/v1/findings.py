from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from backend.app.models.analysis_schemas import Finding
from backend.app.agents.analysis_flow import DeploySafeAnalysisFlow
from backend.app.services.risk_engine import RiskEngine
from backend.app.core.logging import logger

router = APIRouter()

class UpdateFindingStatusPayload(BaseModel):
    status: str = Field(description="Updated status: VALIDATED, NEEDS_REVIEW, DISMISSED")
    reason: Optional[str] = Field(default=None, description="Auditable reasoning for manual status override")

@router.get("", response_model=List[Finding])
def list_findings(
    severity: Optional[str] = Query(None, description="Filter by severity: CRITICAL, HIGH, MEDIUM, LOW"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status: VALIDATED, NEEDS_REVIEW, DUPLICATE, REJECTED, DISMISSED"),
    agent: Optional[str] = Query(None, description="Filter by agent name"),
    file: Optional[str] = Query(None, description="Filter by file path"),
    repository: Optional[str] = Query(None, description="Filter by repository name or id"),
    search: Optional[str] = Query(None, description="Search keyword in title, summary, or file path")
):
    """
    Returns filtered list of findings across all repository analysis runs,
    enabling global triage and multi-attribute discovery.
    """
    reports = DeploySafeAnalysisFlow.list_reports()
    all_findings: List[Finding] = []
    seen_ids = set()

    # Most recent reports first
    reports = sorted(reports, key=lambda r: r.analyzed_at, reverse=True)
    for r in reports:
        for f in r.findings:
            if f.id not in seen_ids:
                seen_ids.add(f.id)
                all_findings.append(f)

    # Apply filters
    filtered = all_findings
    if severity:
        filtered = [f for f in filtered if f.severity.upper() == severity.upper()]
    if category:
        filtered = [f for f in filtered if f.category.upper() == category.upper()]
    if status:
        filtered = [f for f in filtered if f.status.upper() == status.upper()]
    if agent:
        filtered = [f for f in filtered if agent.lower() in f.agent.lower()]
    if file:
        filtered = [f for f in filtered if file.lower() in f.file_path.lower()]
    if repository:
        filtered = [f for f in filtered if repository.lower() in f.repository_id.lower()]
    if search:
        s = search.lower()
        filtered = [
            f for f in filtered
            if s in f.title.lower() or s in f.summary.lower() or s in f.file_path.lower()
        ]

    return filtered

@router.get("/{finding_id}", response_model=Finding)
def get_finding(finding_id: str):
    """
    Returns complete details, evidence items, and score contribution for a specific finding.
    """
    reports = DeploySafeAnalysisFlow.list_reports()
    for r in reports:
        for f in r.findings:
            if f.id == finding_id:
                return f

    raise HTTPException(status_code=404, detail=f"Finding '{finding_id}' not found.")

@router.patch("/{finding_id}/status", response_model=Finding)
def update_finding_status(finding_id: str, payload: UpdateFindingStatusPayload):
    """
    Allows developers/reviewers to mark findings as VALIDATED, NEEDS_REVIEW, or DISMISSED.
    Triggers deterministic risk score recalculation on the parent report.
    """
    valid_statuses = {"VALIDATED", "NEEDS_REVIEW", "DISMISSED"}
    status_upper = payload.status.upper()
    if status_upper not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{payload.status}'. Allowed: {', '.join(valid_statuses)}"
        )

    target_report = None
    target_finding = None

    reports = DeploySafeAnalysisFlow.list_reports()
    for r in reports:
        for f in r.findings:
            if f.id == finding_id:
                target_finding = f
                target_report = r
                break
        if target_finding:
            break

    if not target_finding or not target_report:
        raise HTTPException(status_code=404, detail=f"Finding '{finding_id}' not found.")

    # Update finding
    target_finding.status = status_upper
    if payload.reason:
        target_finding.validation_reason = payload.reason

    # Recalculate deterministic risk score
    risk_eval = RiskEngine.evaluate(target_report.findings)
    target_report.risk_score = risk_eval.risk_score
    target_report.risk_level = risk_eval.risk_level
    target_report.score_breakdown = risk_eval.model_dump()

    # Sync with run if stored
    target_run = DeploySafeAnalysisFlow.get_run(target_report.run_id)
    if target_run:
        target_run.risk_score = risk_eval.risk_score
        target_run.risk_level = risk_eval.risk_level

    # Update validated/needs_review lists
    target_report.validated_findings = [f for f in target_report.findings if f.status == "VALIDATED"]
    target_report.needs_review_findings = [f for f in target_report.findings if f.status == "NEEDS_REVIEW"]
    target_report.rejected_findings = [
        f for f in target_report.findings if f.status in ("REJECTED", "INSUFFICIENT_EVIDENCE")
    ]

    logger.info("Updated finding %s to %s. Recalculated report %s risk score: %s",
                finding_id, status_upper, target_report.run_id, target_report.risk_score)

    return target_finding
