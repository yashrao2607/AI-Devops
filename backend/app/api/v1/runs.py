from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field
from backend.app.models.analysis_schemas import (
    AnalysisRun,
    AnalysisReport,
    Finding,
    RunComparisonResult
)
from backend.app.agents.analysis_flow import DeploySafeAnalysisFlow
from backend.app.services.report_service import ReportService
from backend.app.services.comparison import ComparisonService
from backend.app.core.logging import logger

router = APIRouter()

class UpdateFindingStatusRequest(BaseModel):
    status: str = Field(description="New status: VALIDATED, NEEDS_REVIEW, DISMISSED")
    reason: Optional[str] = Field(default=None, description="Developer explanation for status update")

@router.get("", response_model=List[Dict[str, Any]])
def list_runs():
    """Returns chronological list of all analysis runs with deterministic risk scores."""
    reports = DeploySafeAnalysisFlow.list_reports()
    # Sort descending
    reports = sorted(reports, key=lambda r: r.analyzed_at, reverse=True)
    results = []
    for r in reports:
        results.append({
            "run_id": r.run_id,
            "repository_id": r.repository_id,
            "repository_name": r.repository_name,
            "branch": r.branch or "main",
            "commit_sha": r.commit_sha or "HEAD",
            "risk_score": r.risk_score,
            "risk_level": r.risk_level,
            "findings_count": len(r.findings),
            "validated_count": len(r.validated_findings),
            "needs_review_count": len(r.needs_review_findings),
            "rejected_count": len(r.rejected_findings),
            "status": r.status,
            "duration_seconds": r.duration_seconds,
            "analyzed_at": r.analyzed_at.isoformat()
        })
    return results

@router.get("/{run_id}", response_model=AnalysisRun)
def get_run_details(run_id: str):
    """Returns runtime telemetry, per-agent execution times, and tools called for a run."""
    run = DeploySafeAnalysisFlow.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return run

@router.get("/{run_id}/summary")
def get_run_summary(run_id: str):
    """Returns executive risk summary, level, and mathematical score breakdown."""
    report = DeploySafeAnalysisFlow.get_report(run_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report for run '{run_id}' not found.")
    
    return {
        "run_id": report.run_id,
        "repository_id": report.repository_id,
        "repository_name": report.repository_name,
        "risk_score": report.risk_score,
        "risk_level": report.risk_level,
        "summary": report.summary,
        "score_breakdown": report.score_breakdown,
        "dedup_summary": report.dedup_summary,
        "severity_counts": report.finding_counts_by_severity,
        "recommendations": report.recommendations
    }

@router.get("/{run_id}/findings", response_model=List[Finding])
def get_run_findings(
    run_id: str,
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"),
    status: Optional[str] = Query(None, description="Filter by status (VALIDATED, NEEDS_REVIEW, DUPLICATE, REJECTED, DISMISSED)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    agent: Optional[str] = Query(None, description="Filter by reporting agent"),
    search: Optional[str] = Query(None, description="Search keyword in title, summary, or file path")
):
    """Returns findings for a specific run with multi-attribute filtering."""
    report = DeploySafeAnalysisFlow.get_report(run_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    findings = report.findings

    if severity:
        findings = [f for f in findings if f.severity.upper() == severity.upper()]
    if status:
        findings = [f for f in findings if f.status.upper() == status.upper()]
    if category:
        findings = [f for f in findings if f.category.upper() == category.upper()]
    if agent:
        findings = [f for f in findings if agent.lower() in f.agent.lower()]
    if search:
        s = search.lower()
        findings = [
            f for f in findings
            if s in f.title.lower() or s in f.summary.lower() or s in f.file_path.lower()
        ]

    return findings

@router.get("/{run_id}/report")
def get_formatted_report(
    run_id: str,
    format: str = Query("json", description="Export format: json, markdown, html")
):
    """Returns the finalized report in JSON, Markdown, or styled HTML."""
    report = DeploySafeAnalysisFlow.get_report(run_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report for run '{run_id}' not found.")

    fmt = format.lower()
    if fmt == "markdown" or fmt == "md":
        md_text = ReportService.generate_markdown(report)
        return Response(content=md_text, media_type="text/markdown")
    elif fmt == "html":
        html_text = ReportService.generate_html(report)
        return Response(content=html_text, media_type="text/html")
    else:
        return report


@router.get("/{run_id}/compare", response_model=RunComparisonResult)
def compare_run(
    run_id: str,
    base_run_id: Optional[str] = Query(None, description="Optional baseline run ID. If omitted, uses the immediate previous run for the repository.")
):
    """
    Compares the specified run against a baseline run (Steps 13 & 14).
    Categorizes findings into resolved, new, persistent, changed, and computes deterministic score delta.
    """
    target_report = DeploySafeAnalysisFlow.get_report(run_id)
    if not target_report:
        raise HTTPException(status_code=404, detail=f"Target report for run '{run_id}' not found.")

    base_report = None
    if base_run_id:
        base_report = DeploySafeAnalysisFlow.get_report(base_run_id)
        if not base_report:
            raise HTTPException(status_code=404, detail=f"Baseline report for run '{base_run_id}' not found.")
    else:
        all_reports = DeploySafeAnalysisFlow.list_reports()
        prior_reports = [
            r for r in all_reports
            if r.repository_id == target_report.repository_id and r.run_id != target_report.run_id
        ]
        if prior_reports:
            prior_reports.sort(key=lambda r: r.analyzed_at, reverse=True)
            base_report = prior_reports[0]

    return ComparisonService.compare_reports(target_report, base_report)
