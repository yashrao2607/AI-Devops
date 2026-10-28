"""
DeploySafe Deterministic Deployment Gate Policy Engine.
Evaluates analysis reports and risk scores against configurable project policies
to determine whether code is ALLOWED, REQUIRES REVIEW, or is BLOCKED from deployment.
"""

import os
from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.core.logging import logger


class GatePolicyConfig(BaseModel):
    """
    Configurable deployment gate thresholds.
    Defaults represent sensible project security standards but can be customized.
    """
    max_risk_score: float = Field(
        default=65.0,
        description="Scores strictly above this threshold are BLOCKED."
    )
    review_threshold: float = Field(
        default=45.0,
        description="Scores between review_threshold and max_risk_score require manual team review."
    )
    block_on_critical: bool = Field(
        default=True,
        description="If True, any validated CRITICAL finding immediately BLOCKS the gate regardless of score."
    )
    max_high_count: int = Field(
        default=2,
        description="Maximum allowed validated HIGH severity findings before blocking."
    )


class GateResult(BaseModel):
    """Evaluation decision produced by the Gate Policy Engine."""
    allowed: bool
    status: Literal["ALLOWED", "REVIEW_REQUIRED", "BLOCKED"]
    reasons: List[str]
    exit_code: int  # 0 = Allowed / Review, 1 = Blocked
    risk_score: float
    policy_applied: GatePolicyConfig


class GatePolicyEngine:
    """
    Deterministic gate decision engine.
    Separates risk analysis (what risks exist) from release policy (what actions to take).
    """

    @classmethod
    def get_default_policy(cls) -> GatePolicyConfig:
        max_risk = float(os.getenv("DEPLOYSAFE_GATE_MAX_RISK", "65.0"))
        review_thresh = float(os.getenv("DEPLOYSAFE_GATE_REVIEW_THRESHOLD", "45.0"))
        block_crit = os.getenv("DEPLOYSAFE_GATE_BLOCK_CRITICAL", "true").lower() in ("true", "1", "yes")
        max_high = int(os.getenv("DEPLOYSAFE_GATE_MAX_HIGH", "2"))
        return GatePolicyConfig(
            max_risk_score=max_risk,
            review_threshold=review_thresh,
            block_on_critical=block_crit,
            max_high_count=max_high
        )

    @classmethod
    def policy_from_repo_config(cls, repo_config: Any) -> GatePolicyConfig:
        """Derives a deterministic gate policy from custom repository configuration."""
        default = cls.get_default_policy()
        if not repo_config:
            return default
        max_risk = getattr(repo_config, "risk_threshold", default.max_risk_score)
        block_crit = getattr(repo_config, "block_on_critical", default.block_on_critical)
        review_thresh = max(10.0, round(max_risk * 0.7, 1))
        return GatePolicyConfig(
            max_risk_score=float(max_risk),
            review_threshold=float(review_thresh),
            block_on_critical=bool(block_crit),
            max_high_count=1 if getattr(repo_config, "block_on_high", False) else default.max_high_count
        )

    @classmethod
    def evaluate(
        cls,
        risk_score: float,
        finding_counts: Dict[str, int],
        policy: Optional[GatePolicyConfig] = None
    ) -> GateResult:
        """
        Evaluates risk score and finding distribution against the specified gate policy.
        """
        active_policy = policy or cls.get_default_policy()
        reasons: List[str] = []
        is_blocked = False
        requires_review = False

        crit_count = finding_counts.get("CRITICAL", 0)
        high_count = finding_counts.get("HIGH", 0)

        # Rule 1: Critical Severity Guard
        if active_policy.block_on_critical and crit_count > 0:
            is_blocked = True
            reasons.append(f"Blocked: Found {crit_count} validated CRITICAL deployment risks.")

        # Rule 2: High Severity Count Threshold
        if high_count > active_policy.max_high_count:
            is_blocked = True
            reasons.append(
                f"Blocked: Found {high_count} HIGH severity findings, exceeding policy allowance of {active_policy.max_high_count}."
            )

        # Rule 3: Overall Risk Score Gating
        if risk_score > active_policy.max_risk_score:
            is_blocked = True
            reasons.append(
                f"Blocked: Overall risk score ({risk_score:.1f}/100) exceeds maximum allowable gate threshold ({active_policy.max_risk_score:.1f})."
            )
        elif risk_score >= active_policy.review_threshold:
            requires_review = True
            reasons.append(
                f"Review Required: Risk score ({risk_score:.1f}/100) falls in the team review zone [{active_policy.review_threshold:.1f} - {active_policy.max_risk_score:.1f}]."
            )

        # Determine final status and exit code
        if is_blocked:
            status: Literal["ALLOWED", "REVIEW_REQUIRED", "BLOCKED"] = "BLOCKED"
            allowed = False
            exit_code = 1
        elif requires_review:
            status = "REVIEW_REQUIRED"
            allowed = True  # CI can proceed or require review depending on workflow config
            exit_code = 0
            if not reasons:
                reasons.append("Manual review suggested before triggering production rollout.")
        else:
            status = "ALLOWED"
            allowed = True
            exit_code = 0
            reasons.append(f"Passed: Risk score ({risk_score:.1f}/100) is within safe deployment limits.")

        logger.info("GatePolicyEngine decision: status=%s, exit_code=%d, reasons=%s",
                    status, exit_code, reasons)

        return GateResult(
            allowed=allowed,
            status=status,
            reasons=reasons,
            exit_code=exit_code,
            risk_score=risk_score,
            policy_applied=active_policy
        )
