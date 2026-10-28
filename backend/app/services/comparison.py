from typing import Optional, Dict, Any, List, Tuple
from backend.app.models.analysis_schemas import (
    AnalysisReport,
    Finding,
    RunComparisonResult,
    ComparisonFindingItem
)
from backend.app.core.logging import logger


def compute_finding_fingerprint(finding: Finding) -> str:
    """
    Computes a deterministic content-and-location fingerprint for a finding.
    Combines normalized relative file path, line_start, category, and rule_id or core title words.
    Does NOT depend purely on LLM generated titles.
    """
    norm_path = (finding.file_path or "").strip().replace("\\", "/").lower()
    line = str(finding.line_start if finding.line_start is not None else 0)
    category = (finding.category or "").strip().upper()
    identifier = (finding.rule_id or "").strip().lower()
    if not identifier:
        # Fallback to normalized alphanumeric title keywords
        clean_title = "".join(c for c in (finding.title or "").lower() if c.isalnum() or c.isspace())
        words = clean_title.split()
        identifier = "-".join(words[:5]) if words else "finding"
    return f"{norm_path}::{line}::{category}::{identifier}"


def _to_comparison_item(finding: Finding, fingerprint: str) -> ComparisonFindingItem:
    return ComparisonFindingItem(
        fingerprint=fingerprint,
        finding_id=finding.id,
        title=finding.title,
        file_path=finding.file_path,
        line_start=finding.line_start,
        severity=finding.severity,
        category=finding.category,
        status=finding.status,
        score_contribution=getattr(finding, "score_contribution", 0.0)
    )


class ComparisonService:
    """
    Service responsible for deterministic before/after run comparison.
    Satisfies Step 13 & Step 14 of Phase 6:
    - Fingerprint-based finding matching (file, line, category, rule)
    - Categorization: Resolved, New, Persistent, Changed
    - Delta tracking: Score change, trend, baseline availability
    - Zero fabrication: If no prior run exists, reports 'No previous analysis available.'
    """

    @classmethod
    def compare_reports(
        cls,
        target_report: AnalysisReport,
        base_report: Optional[AnalysisReport] = None
    ) -> RunComparisonResult:
        """
        Compares target_report (current run) against base_report (baseline/prior run).
        """
        if not base_report:
            return RunComparisonResult(
                has_baseline=False,
                target_run_id=target_report.run_id,
                repository_id=target_report.repository_id,
                repository_name=target_report.repository_name,
                base_score=None,
                target_score=target_report.risk_score,
                score_delta=None,
                risk_trend="INITIAL_BASELINE",
                base_findings_count=0,
                target_findings_count=len(target_report.findings),
                resolved_count=0,
                new_count=0,
                persistent_count=0,
                changed_count=0,
                resolved_findings=[],
                new_findings=[],
                persistent_findings=[],
                changed_findings=[],
                message="No previous analysis available."
            )

        # Index base findings by fingerprint
        base_map: Dict[str, Finding] = {}
        for f in base_report.findings:
            fp = compute_finding_fingerprint(f)
            base_map[fp] = f

        # Index target findings by fingerprint
        target_map: Dict[str, Finding] = {}
        for f in target_report.findings:
            fp = compute_finding_fingerprint(f)
            target_map[fp] = f

        resolved_items: List[ComparisonFindingItem] = []
        new_items: List[ComparisonFindingItem] = []
        persistent_items: List[ComparisonFindingItem] = []
        changed_items: List[Dict[str, Any]] = []

        # Find Resolved findings (in base, absent in target)
        for fp, base_f in base_map.items():
            if fp not in target_map:
                resolved_items.append(_to_comparison_item(base_f, fp))

        # Find New, Persistent, and Changed findings
        for fp, target_f in target_map.items():
            if fp not in base_map:
                new_items.append(_to_comparison_item(target_f, fp))
            else:
                base_f = base_map[fp]
                # Check for changes in severity, status, or score
                severity_changed = base_f.severity != target_f.severity
                status_changed = base_f.status != target_f.status
                score_changed = getattr(base_f, "score_contribution", 0.0) != getattr(target_f, "score_contribution", 0.0)

                if severity_changed or status_changed or score_changed:
                    changed_items.append({
                        "fingerprint": fp,
                        "finding_id": target_f.id,
                        "title": target_f.title,
                        "file_path": target_f.file_path,
                        "line_start": target_f.line_start,
                        "category": target_f.category,
                        "base_severity": base_f.severity,
                        "target_severity": target_f.severity,
                        "base_status": base_f.status,
                        "target_status": target_f.status,
                        "base_score_contribution": getattr(base_f, "score_contribution", 0.0),
                        "target_score_contribution": getattr(target_f, "score_contribution", 0.0),
                    })
                else:
                    persistent_items.append(_to_comparison_item(target_f, fp))

        # Calculate score delta
        # If target score is lower than base score, delta is negative -> improvement
        score_delta = round(target_report.risk_score - base_report.risk_score, 2)
        if score_delta < 0:
            trend = "IMPROVED"
        elif score_delta > 0:
            trend = "DEGRADED"
        else:
            trend = "UNCHANGED"

        return RunComparisonResult(
            has_baseline=True,
            base_run_id=base_report.run_id,
            target_run_id=target_report.run_id,
            repository_id=target_report.repository_id,
            repository_name=target_report.repository_name,
            base_score=base_report.risk_score,
            target_score=target_report.risk_score,
            score_delta=score_delta,
            risk_trend=trend,
            base_findings_count=len(base_report.findings),
            target_findings_count=len(target_report.findings),
            resolved_count=len(resolved_items),
            new_count=len(new_items),
            persistent_count=len(persistent_items),
            changed_count=len(changed_items),
            resolved_findings=resolved_items,
            new_findings=new_items,
            persistent_findings=persistent_items,
            changed_findings=changed_items,
            message=f"Comparison completed against base run {base_report.run_id}."
        )
