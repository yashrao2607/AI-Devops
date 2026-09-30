from datetime import datetime
from typing import List, Dict
from backend.app.models.analysis_schemas import Finding, AnalysisReport, AnalysisContext
from backend.app.core.logging import logger

class ReportGenerationAgent:
    """
    Report Agent (Step 21 of Phase 3).
    Synthesizes findings into an executive deployment readiness report.
    Does NOT calculate final 0-100 mathematical risk score (belonging to Phase 4).
    """

    @staticmethod
    def generate_report(
        context: AnalysisContext,
        run_id: str,
        findings: List[Finding],
        agents_executed: List[str],
        tools_used: List[str],
        duration_seconds: float
    ) -> AnalysisReport:
        validated = [f for f in findings if f.status == "VALIDATED"]
        needs_review = [f for f in findings if f.status == "NEEDS_REVIEW"]
        rejected = [f for f in findings if f.status in ("REJECTED", "INSUFFICIENT_EVIDENCE")]

        # Compute accurate counts by severity for validated + needs_review
        counts: Dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for f in validated + needs_review:
            if f.severity in counts:
                counts[f.severity] += 1

        # Recommendations from validated findings
        recommendations = []
        for f in validated:
            if f.recommendation and f.recommendation not in recommendations:
                recommendations.append(f"{f.title}: {f.recommendation}")

        # Summary text
        crit_count = counts["CRITICAL"]
        high_count = counts["HIGH"]
        if crit_count > 0:
            summary = (
                f"DEPLOYMENT BLOCKED: Identified {crit_count} CRITICAL and {high_count} HIGH risk deployment findings "
                f"across {len(context.all_files)} repository files. Critical issues must be resolved prior to release."
            )
        elif high_count > 0:
            summary = (
                f"HIGH RISK DETECTED: Discovered {high_count} high-severity operational or configuration risks. "
                f"Recommended fixes should be reviewed before production promotion."
            )
        elif len(validated) > 0:
            summary = (
                f"MODERATE / LOW RISK: Discovered {len(validated)} validated minor findings. "
                f"Application structure appears largely ready for deployment."
            )
        else:
            summary = "CLEAN DEPLOYMENT READINESS: No deployment-blocking issues discovered across analyzed files."

        report = AnalysisReport(
            run_id=run_id,
            repository_id=context.repository_id,
            repository_name=context.repository_name,
            commit_sha=context.commit_sha,
            branch=context.branch,
            analyzed_at=datetime.utcnow(),
            duration_seconds=duration_seconds,
            status="COMPLETED",
            agents_executed=agents_executed,
            tools_used=tools_used,
            findings=findings,
            validated_findings=validated,
            needs_review_findings=needs_review,
            rejected_findings=rejected,
            finding_counts_by_severity=counts,
            summary=summary,
            recommendations=recommendations[:8]
        )

        logger.info(
            "ReportAgent generated report for run '%s': %d validated findings (Crit: %d, High: %d)",
            run_id, len(validated), crit_count, high_count
        )
        return report
