from typing import Dict, Any, List, Optional
from fastapi import APIRouter
from backend.app.models.analysis_schemas import DashboardSummary, Finding
from backend.app.agents.analysis_flow import DeploySafeAnalysisFlow

router = APIRouter()

@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary():
    """
    Returns aggregated metrics across all analyzed repositories and runs (Phase 4 Part 12).
    Includes latest risk score, severity distributions, recent runs, and top validated findings.
    """
    runs = DeploySafeAnalysisFlow.list_runs()
    reports = DeploySafeAnalysisFlow.list_reports()

    if not reports:
        return DashboardSummary(
            total_runs=0,
            latest_run_id=None,
            latest_risk_score=0.0,
            latest_risk_level="LOW",
            total_findings_detected=0,
            validated_findings_count=0,
            severity_distribution={"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
            status_distribution={"VALIDATED": 0, "NEEDS_REVIEW": 0, "DUPLICATE": 0, "REJECTED": 0, "DISMISSED": 0},
            recent_runs=[],
            top_findings=[]
        )

    # Sort reports by analyzed_at descending
    sorted_reports = sorted(reports, key=lambda r: r.analyzed_at, reverse=True)
    latest_report = sorted_reports[0]

    # Aggregate finding metrics across all reports
    all_findings: List[Finding] = []
    sev_dist = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    status_dist = {"VALIDATED": 0, "NEEDS_REVIEW": 0, "DUPLICATE": 0, "REJECTED": 0, "DISMISSED": 0}

    for rep in sorted_reports:
        for f in rep.findings:
            all_findings.append(f)
            sev = f.severity.upper() if f.severity.upper() in sev_dist else "MEDIUM"
            sev_dist[sev] += 1
            st = f.status.upper() if f.status.upper() in status_dist else "NEEDS_REVIEW"
            status_dist[st] += 1

    # Formulate recent runs list
    recent_runs = []
    for r in sorted_reports[:10]:
        recent_runs.append({
            "run_id": r.run_id,
            "repository_id": r.repository_id,
            "repository_name": r.repository_name,
            "branch": r.branch or "main",
            "commit_sha": r.commit_sha or "HEAD",
            "risk_score": r.risk_score,
            "risk_level": r.risk_level,
            "findings_count": len(r.findings),
            "validated_count": len(r.validated_findings),
            "status": r.status,
            "analyzed_at": r.analyzed_at.isoformat(),
            "duration_seconds": r.duration_seconds
        })

    # Top validated findings sorted by severity (CRITICAL > HIGH > MEDIUM > LOW)
    rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    top_findings = sorted(
        latest_report.validated_findings,
        key=lambda f: (rank.get(f.severity.upper(), 0), f.score_contribution),
        reverse=True
    )[:10]

    return DashboardSummary(
        total_runs=len(sorted_reports),
        latest_run_id=latest_report.run_id,
        latest_repository_id=latest_report.repository_id,
        latest_risk_score=latest_report.risk_score,
        latest_risk_level=latest_report.risk_level,
        total_findings_detected=len(all_findings),
        validated_findings_count=sum(1 for f in all_findings if f.status == "VALIDATED"),
        severity_distribution=sev_dist,
        status_distribution=status_dist,
        recent_runs=recent_runs,
        top_findings=top_findings
    )
