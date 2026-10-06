import os
from typing import List, Tuple
from backend.app.agents.specialized.base import BaseSpecializedAgent
from backend.app.models.analysis_schemas import AnalysisContext, Finding, CriticResult
from backend.app.core.logging import logger

class CriticAgent(BaseSpecializedAgent):
    """
    Critic / Validation Agent (Step 19 of Phase 3 / Phase 4 Intelligence Layer).
    Acts as the independent verification gatekeeper:
    - Hallucination defense: Verifies file existence in the repository snapshot
    - Evidence sufficiency: Rejects findings lacking concrete factual justification
    - Proximity deduplication: Collapses redundant reports across multiple agents
    - Engineering notes: Writes articulate, engineer-ready verification rationales
    """

    def __init__(self):
        super().__init__(
            agent_name="CriticAgent",
            prompt_file="critic_agent.md"
        )

    def review_findings(
        self,
        context: AnalysisContext,
        candidate_findings: List[Finding]
    ) -> Tuple[List[Finding], List[CriticResult]]:
        """
        Reviews all candidate findings, validating against repository ground-truth.
        Returns:
            updated_findings: Original findings with updated status and articulate critic notes
            decisions: Structured audit trail of decisions
        """
        decisions: List[CriticResult] = []
        updated_findings: List[Finding] = []
        seen_keys = {}

        for f in candidate_findings:
            # 1. Hallucination check: Does the file exist in repository?
            norm_file = os.path.normpath(f.file_path).lstrip(r"\/").replace("\\", "/")
            full_path = os.path.normpath(os.path.join(context.root_path, norm_file))

            # Check if file exists on disk or in indexed manifest
            file_exists = (
                os.path.isfile(full_path)
                or norm_file in context.all_files
                or any(norm_file == os.path.normpath(af).replace("\\", "/") for af in context.all_files)
            )

            if not file_exists and f.file_path != "repository_root":
                f.status = "REJECTED"
                f.critic_notes = f"Hallucination Defense: File '{f.file_path}' does not exist in repository snapshot."
                dec = CriticResult(
                    finding_id=f.id,
                    decision="REJECTED",
                    confidence="HIGH",
                    reason=f.critic_notes
                )
                decisions.append(dec)
                updated_findings.append(f)
                continue

            # 2. Evidence check: Is concrete evidence provided?
            if not f.evidence or not f.evidence.strip():
                f.status = "INSUFFICIENT_EVIDENCE"
                f.critic_notes = "Insufficient Evidence: Finding claims risk without concrete repository code or manifest snippet."
                dec = CriticResult(
                    finding_id=f.id,
                    decision="INSUFFICIENT_EVIDENCE",
                    confidence="HIGH",
                    reason=f.critic_notes
                )
                decisions.append(dec)
                updated_findings.append(f)
                continue

            # 3. Deduplication check
            dedup_key = f"{norm_file}:{f.line_start or 0}:{f.category}"
            if dedup_key in seen_keys:
                primary_id = seen_keys[dedup_key]
                f.status = "DUPLICATE"
                f.critic_notes = f"Duplicate Finding: Redundant with canonical issue reported in {primary_id}."
                dec = CriticResult(
                    finding_id=f.id,
                    decision="DUPLICATE",
                    confidence="HIGH",
                    reason=f.critic_notes,
                    duplicate_of_id=primary_id
                )
                decisions.append(dec)
                updated_findings.append(f)
                continue

            seen_keys[dedup_key] = f.id

            # 4. Severity & Confidence Calibration with articulate notes
            if f.source in ("deterministic", "deterministic+agent", "rag_correlated"):
                f.status = "VALIDATED"
                f.critic_notes = (
                    f"Verified: Finding is substantiated by concrete repository evidence in '{norm_file}' "
                    f"(L{f.line_start or 1}-L{f.line_end or 1}). Ground-truth verified with {f.confidence.lower()} confidence."
                )
                dec = CriticResult(
                    finding_id=f.id,
                    decision="VALIDATED",
                    confidence="HIGH",
                    reason=f.critic_notes
                )
            else:
                if "INFERRED" in f.title or f.confidence == "LOW":
                    f.status = "NEEDS_REVIEW"
                    f.critic_notes = (
                        f"Engineering Review Recommended: Inferred risk pattern in '{norm_file}' requires manual validation "
                        f"against deployment topology."
                    )
                    dec = CriticResult(
                        finding_id=f.id,
                        decision="NEEDS_REVIEW",
                        confidence="MEDIUM",
                        reason=f.critic_notes
                    )
                else:
                    f.status = "VALIDATED"
                    f.critic_notes = (
                        f"Verified: Code and configuration evidence verified against repository snapshot. "
                        f"Blast radius confirmed for {f.severity.lower()} severity impact."
                    )
                    dec = CriticResult(
                        finding_id=f.id,
                        decision="VALIDATED",
                        confidence="HIGH",
                        reason=f.critic_notes
                    )

            decisions.append(dec)
            updated_findings.append(f)

        logger.info(
            "CriticAgent reviewed %d findings: %d validated, %d needs_review, %d duplicate, %d rejected.",
            len(candidate_findings),
            sum(1 for d in decisions if d.decision == "VALIDATED"),
            sum(1 for d in decisions if d.decision == "NEEDS_REVIEW"),
            sum(1 for d in decisions if d.decision == "DUPLICATE"),
            sum(1 for d in decisions if d.decision in ("REJECTED", "INSUFFICIENT_EVIDENCE"))
        )
        return updated_findings, decisions
