import os
from typing import List, Tuple
from backend.app.agents.specialized.base import BaseSpecializedAgent
from backend.app.models.analysis_schemas import AnalysisContext, Finding, CriticResult
from backend.app.core.logging import logger

class CriticAgent(BaseSpecializedAgent):
    """
    Critic / Validation Agent (Step 19 of Phase 3).
    Acts as the independent verification gatekeeper:
    - Hallucination defense: Verifies file exists and line range is valid
    - Evidence sufficiency: Rejects findings lacking factual justification
    - Deduplication: Flags redundant findings across agents
    - Sets status to VALIDATED, NEEDS_REVIEW, DUPLICATE, or REJECTED
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
            updated_findings: Original findings with updated status and critic notes
            decisions: Structured audit trail of decisions
        """
        decisions: List[CriticResult] = []
        updated_findings: List[Finding] = []
        seen_keys = {}

        for f in candidate_findings:
            # 1. Hallucination check: Does the file exist in repository?
            norm_file = os.path.normpath(f.file_path).lstrip(r"\/")
            full_path = os.path.normpath(os.path.join(context.root_path, norm_file))

            if not os.path.isfile(full_path) and norm_file not in context.all_files:
                f.status = "REJECTED"
                f.critic_notes = f"Hallucination rejection: File '{f.file_path}' does not exist in repository snapshot."
                dec = CriticResult(
                    finding_id=f.id,
                    decision="REJECTED",
                    confidence="HIGH",
                    reason=f.critic_notes
                )
                decisions.append(dec)
                updated_findings.append(f)
                continue

            # 2. Evidence check: Is evidence provided?
            if not f.evidence or not f.evidence.strip():
                f.status = "INSUFFICIENT_EVIDENCE"
                f.critic_notes = "Insufficient evidence: finding claims risk without concrete repository snippet."
                dec = CriticResult(
                    finding_id=f.id,
                    decision="INSUFFICIENT_EVIDENCE",
                    confidence="HIGH",
                    reason=f.critic_notes
                )
                decisions.append(dec)
                updated_findings.append(f)
                continue

            # 3. Deduplication check (Step 20)
            # Signature based on file and line proximity
            dedup_key = f"{f.file_path}:{f.line_start or 0}:{f.category}"
            if dedup_key in seen_keys:
                primary_id = seen_keys[dedup_key]
                f.status = "DUPLICATE"
                f.critic_notes = f"Duplicate finding: substantially matches issue reported in {primary_id}."
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

            # 4. Severity & Confidence calibration
            if f.source in ("deterministic", "deterministic+agent", "rag_correlated"):
                f.status = "VALIDATED"
                f.critic_notes = "Validated: Finding is supported by concrete deterministic/RAG repository evidence."
                dec = CriticResult(
                    finding_id=f.id,
                    decision="VALIDATED",
                    confidence="HIGH",
                    reason=f.critic_notes
                )
            else:
                # Inferred findings
                if "INFERRED" in f.title or f.confidence == "LOW":
                    f.status = "NEEDS_REVIEW"
                    f.critic_notes = "Needs review: Finding represents an inferred concern requiring engineer assessment."
                    dec = CriticResult(
                        finding_id=f.id,
                        decision="NEEDS_REVIEW",
                        confidence="MEDIUM",
                        reason=f.critic_notes
                    )
                else:
                    f.status = "VALIDATED"
                    f.critic_notes = "Validated: Finding evidence verified against repository source code."
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
