import os
import yaml
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from backend.app.core.logging import logger

APPROVED_CHECKERS = {
    "code_analysis",
    "dependency_analysis",
    "configuration_analysis",
    "test_analysis",
    "rag_analysis",
    "security_analysis"
}

class DeploySafeRepoConfig(BaseModel):
    """
    Typed, schema-validated repository configuration from deploysafe.yml.
    Implements Phase 7 Step 11 & Step 12:
    - Bounded risk thresholds (10.0 <= threshold <= 90.0)
    - Validated ignored paths (path traversal rejected)
    - Approved checks only
    - Strictly untrusted input validation
    """
    version: int = Field(default=1, description="Configuration specification version")
    risk_threshold: float = Field(
        default=50.0,
        ge=10.0,
        le=90.0,
        description="Repository deployment risk policy ceiling (10 to 90)"
    )
    block_on_critical: bool = Field(
        default=True,
        description="Whether any validated CRITICAL finding blocks deployment regardless of score"
    )
    block_on_high: bool = Field(
        default=False,
        description="Whether any validated HIGH finding triggers REVIEW_REQUIRED"
    )
    ignored_paths: List[str] = Field(
        default_factory=list,
        description="Relative file paths or patterns ignored during non-security analysis"
    )
    required_checks: List[str] = Field(
        default_factory=list,
        description="Specific checks that must succeed for this repository"
    )

    @field_validator("ignored_paths")
    def validate_ignored_paths(cls, paths: List[str]) -> List[str]:
        cleaned = []
        for p in paths:
            norm = p.strip().replace("\\", "/")
            # Reject directory traversal attempts
            if ".." in norm or norm.startswith("/") or norm.startswith("~"):
                logger.warning("Rejected malicious ignored_path in repo config: %s", p)
                continue
            cleaned.append(norm)
        return cleaned

    @field_validator("required_checks")
    def validate_required_checks(cls, checks: List[str]) -> List[str]:
        valid = []
        for c in checks:
            norm = c.strip().lower()
            if norm in APPROVED_CHECKERS:
                valid.append(norm)
            else:
                logger.warning("Rejected unknown/unapproved check in repo config: %s", c)
        return valid


class RepoConfigService:
    """
    Discovers and parses deploysafe.yml from a repository snapshot with defensive validation.
    """

    CONFIG_FILENAMES = ["deploysafe.yml", "deploysafe.yaml", ".deploysafe.yml"]

    @classmethod
    def load_config(cls, repository_root: str) -> DeploySafeRepoConfig:
        """
        Locates and parses repo-level configuration. Returns default safe config if not present or invalid.
        """
        if not repository_root or not os.path.isdir(repository_root):
            return DeploySafeRepoConfig()

        for fname in cls.CONFIG_FILENAMES:
            cpath = os.path.join(repository_root, fname)
            if os.path.isfile(cpath):
                try:
                    with open(cpath, "r", encoding="utf-8", errors="replace") as f:
                        # safe_load forbids arbitrary Python object instantiation
                        raw_data = yaml.safe_load(f)

                    if isinstance(raw_data, dict):
                        # Filter out any unexpected or dangerous top-level keys
                        allowed_keys = DeploySafeRepoConfig.model_fields.keys()
                        safe_dict = {k: v for k, v in raw_data.items() if k in allowed_keys}
                        config = DeploySafeRepoConfig(**safe_dict)
                        logger.info("Loaded custom DeploySafeRepoConfig from %s (threshold=%.1f)",
                                    fname, config.risk_threshold)
                        return config
                except Exception as e:
                    logger.warning("Failed to parse %s defensively; falling back to default: %s", fname, str(e))
                    return DeploySafeRepoConfig()

        return DeploySafeRepoConfig()
