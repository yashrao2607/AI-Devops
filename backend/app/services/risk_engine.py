from typing import List, Dict, Any, Tuple
from backend.app.models.analysis_schemas import Finding, RiskEvaluation, ScoreContributor
from backend.app.core.logging import logger

class RiskEngine:
    """
    Deterministic Deployment-Risk Scoring Engine (Phase 4, Parts 6 - 10).
    Receives validated findings and deterministically computes a normalized 0-100 risk score.
    Zero LLM interference in mathematical scoring.
    """

    # Project-defined severity weights (prd.md §10)
    SEVERITY_WEIGHTS: Dict[str, float] = {
        "CRITICAL": 35.0,
        "HIGH": 25.0,
        "MEDIUM": 15.0,
        "LOW": 7.0
    }

    # Project-defined confidence multipliers
    CONFIDENCE_FACTORS: Dict[str, float] = {
        "HIGH": 1.0,
        "MEDIUM": 0.8,
        "LOW": 0.6
    }

    # Project-defined operational impact multipliers
    IMPACT_FACTORS: Dict[str, float] = {
        "CRITICAL": 1.0,
        "HIGH": 1.0,
        "MEDIUM": 0.8,
        "LOW": 0.6
    }

    @classmethod
    def get_risk_level(cls, score: float) -> str:
        """Categorizes numerical 0-100 score into project-defined risk tiers."""
        if score < 25.0:
            return "LOW"
        elif score < 50.0:
            return "MODERATE"
        elif score < 75.0:
            return "HIGH"
        else:
            return "CRITICAL"

    @classmethod
    def calculate_finding_contribution(cls, finding: Finding) -> float:
        """
        Computes the point contribution of a single finding:
          Points = Severity Weight * Confidence Factor * Impact Factor
        """
        sev_weight = cls.SEVERITY_WEIGHTS.get(finding.severity.upper(), 15.0)
        conf_factor = cls.CONFIDENCE_FACTORS.get(finding.confidence.upper(), 0.8)
        imp_factor = cls.IMPACT_FACTORS.get(finding.impact_level.upper(), 1.0)
        
        raw_points = sev_weight * conf_factor * imp_factor
        return round(raw_points, 1)

    @classmethod
    def evaluate(cls, findings: List[Finding]) -> RiskEvaluation:
        """
        Executes deterministic evaluation across all findings.
        Excludes duplicates, rejected findings, dismissed items, and unvalidated claims.
        """
        contributors: List[ScoreContributor] = []
        excluded_findings: List[Dict[str, str]] = []
        severity_breakdown: Dict[str, float] = {
            "CRITICAL": 0.0,
            "HIGH": 0.0,
            "MEDIUM": 0.0,
            "LOW": 0.0
        }
        total_raw = 0.0

        for f in findings:
            st = f.status.upper()

            # Rule 1: Duplicates contribute 0 points
            if st == "DUPLICATE":
                f.score_contribution = 0.0
                excluded_findings.append({
                    "finding_id": f.id,
                    "title": f.title,
                    "status": st,
                    "reason": f"Excluded as duplicate of primary finding (dedup_group: {f.dedup_group_id or 'merged'})"
                })
                continue

            # Rule 2: Rejected and Insufficient Evidence contribute 0 points
            if st in ("REJECTED", "INSUFFICIENT_EVIDENCE"):
                f.score_contribution = 0.0
                excluded_findings.append({
                    "finding_id": f.id,
                    "title": f.title,
                    "status": st,
                    "reason": "Excluded as rejected by Critic Agent (lacks ground-truth repository evidence)"
                })
                continue

            # Rule 3: Dismissed findings contribute 0 points
            if st == "DISMISSED":
                f.score_contribution = 0.0
                excluded_findings.append({
                    "finding_id": f.id,
                    "title": f.title,
                    "status": st,
                    "reason": "Excluded as dismissed by developer override"
                })
                continue

            # Rule 4: Needs Review findings do not add to validated risk score directly
            if st == "NEEDS_REVIEW":
                f.score_contribution = 0.0
                excluded_findings.append({
                    "finding_id": f.id,
                    "title": f.title,
                    "status": st,
                    "reason": "Excluded from active score pending manual engineer verification (inferred concern)"
                })
                continue

            # Rule 5: VALIDATED findings contribute deterministically
            if st == "VALIDATED":
                pts = cls.calculate_finding_contribution(f)
                f.score_contribution = pts
                total_raw += pts

                sev_key = f.severity.upper() if f.severity.upper() in severity_breakdown else "MEDIUM"
                severity_breakdown[sev_key] = round(severity_breakdown[sev_key] + pts, 1)

                contributors.append(ScoreContributor(
                    finding_id=f.id,
                    title=f.title,
                    severity=f.severity,
                    confidence=f.confidence,
                    impact_level=f.impact_level,
                    points=pts,
                    file_path=f.file_path,
                    line_start=f.line_start
                ))
            else:
                # Fallback for unrecognized status
                f.score_contribution = 0.0
                excluded_findings.append({
                    "finding_id": f.id,
                    "title": f.title,
                    "status": st,
                    "reason": f"Status '{st}' is unverified and excluded from score"
                })

        # Score normalization (bounded between 0.0 and 100.0)
        final_score = min(100.0, max(0.0, round(total_raw, 1)))
        risk_level = cls.get_risk_level(final_score)

        formula_text = (
            "DeploySafe Deterministic Formula: "
            "Score = min(100.0, round(sum(severity_weight * confidence_multiplier * impact_multiplier))). "
            "Weights: Critical=35, High=25, Medium=15, Low=7. "
            "Multipliers: High=1.0, Medium=0.8, Low=0.6. "
            "Only Critic-Validated findings contribute points."
        )

        logger.info(
            "RiskEngine evaluated %d findings: Raw=%.1f, Final Score=%.1f (%s), Contributors=%d, Excluded=%d",
            len(findings), total_raw, final_score, risk_level, len(contributors), len(excluded_findings)
        )

        return RiskEvaluation(
            risk_score=final_score,
            risk_level=risk_level,
            raw_score=round(total_raw, 1),
            contributors=contributors,
            excluded_findings=excluded_findings,
            severity_breakdown=severity_breakdown,
            formula_explanation=formula_text
        )
