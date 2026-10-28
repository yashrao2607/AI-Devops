from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.app.agents.analysis_flow import DeploySafeAnalysisFlow
from backend.app.services.comparison import compute_finding_fingerprint


class RepositoryAnalyticsReport(BaseModel):
    """
    Historical repository risk analytics implementing Phase 7 Step 8 & Step 9.
    Constructed strictly from actual stored runs (zero fabricated history).
    """
    repository_id: str
    total_runs_analyzed: int
    risk_trend: List[Dict[str, Any]]
    category_distribution: Dict[str, int]
    recurring_findings: List[Dict[str, Any]]
    resolution_velocity_pct: float
    average_risk_score: float
    latest_score: Optional[float] = None
    summary: str


class HistoryAnalyticsService:
    """
    Service aggregating longitudinal analysis trends across stored runs.
    """

    @classmethod
    def analyze_repository_history(cls, repository_id: str) -> RepositoryAnalyticsReport:
        reports = DeploySafeAnalysisFlow.list_reports()
        repo_reports = [r for r in reports if r.repository_id == repository_id]

        if not repo_reports:
            return RepositoryAnalyticsReport(
                repository_id=repository_id,
                total_runs_analyzed=0,
                risk_trend=[],
                category_distribution={},
                recurring_findings=[],
                resolution_velocity_pct=0.0,
                average_risk_score=0.0,
                latest_score=None,
                summary=f"No stored runs found for repository '{repository_id}'."
            )

        # Sort chronological (oldest to newest)
        repo_reports.sort(key=lambda r: r.analyzed_at)

        risk_trend = []
        category_counts: Dict[str, int] = {}
        fingerprint_occurrences: Dict[str, Dict[str, Any]] = {}

        total_score = 0.0

        for r in repo_reports:
            total_score += r.risk_score
            risk_trend.append({
                "run_id": r.run_id,
                "risk_score": r.risk_score,
                "risk_level": r.risk_level,
                "analyzed_at": r.analyzed_at.isoformat(),
                "findings_count": len(r.findings)
            })

            # Track categories & recurring issues
            for f in r.findings:
                cat = f.category or "OTHER"
                category_counts[cat] = category_counts.get(cat, 0) + 1

                fp = compute_finding_fingerprint(f)
                if fp not in fingerprint_occurrences:
                    fingerprint_occurrences[fp] = {
                        "fingerprint": fp,
                        "title": f.title,
                        "file_path": f.file_path,
                        "category": f.category,
                        "severity": f.severity,
                        "seen_in_runs": 0,
                        "run_ids": []
                    }
                fingerprint_occurrences[fp]["seen_in_runs"] += 1
                fingerprint_occurrences[fp]["run_ids"].append(r.run_id)

        avg_score = round(total_score / len(repo_reports), 2)
        latest_score = repo_reports[-1].risk_score

        # Recurring findings: seen in >= 2 runs
        recurring = [
            v for v in fingerprint_occurrences.values()
            if v["seen_in_runs"] >= 2
        ]
        recurring.sort(key=lambda x: x["seen_in_runs"], reverse=True)

        # Resolution velocity: findings in first run that are resolved in latest run
        resolution_pct = 0.0
        if len(repo_reports) >= 2:
            first_fps = {compute_finding_fingerprint(f) for f in repo_reports[0].findings}
            latest_fps = {compute_finding_fingerprint(f) for f in repo_reports[-1].findings}
            if first_fps:
                resolved_count = len(first_fps - latest_fps)
                resolution_pct = round((resolved_count / len(first_fps)) * 100.0, 1)

        summary = (
            f"Repository '{repository_id}' has {len(repo_reports)} recorded run(s). "
            f"Average risk score: {avg_score}/100 (Latest: {latest_score}/100). "
            f"{len(recurring)} recurring issue pattern(s) detected across runs."
        )

        return RepositoryAnalyticsReport(
            repository_id=repository_id,
            total_runs_analyzed=len(repo_reports),
            risk_trend=risk_trend,
            category_distribution=category_counts,
            recurring_findings=recurring[:10],
            resolution_velocity_pct=resolution_pct,
            average_risk_score=avg_score,
            latest_score=latest_score,
            summary=summary
        )
