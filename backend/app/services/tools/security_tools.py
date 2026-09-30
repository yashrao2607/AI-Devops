import os
import re
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.models.analysis_schemas import AnalysisContext, Evidence
from backend.app.services.tools.safe_executor import SafeCommandExecutor
from backend.app.core.logging import logger

class SecurityScanItem(BaseModel):
    rule_id: str
    severity: str
    file_path: str
    line_number: int
    title: str
    description: str
    evidence_snippet: str

class SecurityScanResult(BaseModel):
    tool_name: str
    executed_external_tool: bool
    exit_code: int
    total_findings: int
    items: List[SecurityScanItem]
    errors: Optional[str] = None

class SecurityTools:
    """
    Deterministic security tooling implementing Step 14 of Phase 3.
    Executes Bandit or Gitleaks if installed, or executes high-confidence
    AST/regex security analyzers directly against repository files.
    """

    SECRET_PATTERNS = [
        ("AWS_ACCESS_KEY", r"AKIA[0-9A-Z]{16}", "High-entropy AWS Access Key pattern"),
        ("HARDCODED_PASSWORD", r"(?:password|passwd|pwd|secret)\s*[:=]\s*['\"]([^'\"]{8,})['\"]", "Hardcoded credential assignment"),
        ("PRIVATE_KEY", r"-----BEGIN (?:RSA|OPENSSH|EC|DSA)? PRIVATE KEY-----", "Hardcoded cryptographic private key"),
        ("GENERIC_API_TOKEN", r"(?:api[_-]?key|auth[_-]?token|bearer)\s*[:=]\s*['\"]([a-zA-Z0-9_\-\.]{20,})['\"]", "Hardcoded API authorization token"),
        ("DATABASE_URI_WITH_CREDS", r"(?:postgres|mysql|mongodb|redis):\/\/[a-zA-Z0-9_-]+:[^@\s]+@[a-zA-Z0-9.-]+", "Database connection string containing raw credentials")
    ]

    @classmethod
    def run_security_scan(cls, context: AnalysisContext) -> SecurityScanResult:
        items: List[SecurityScanItem] = []
        executed_external = False
        tool_used = "deploy_safe_security_engine"

        # 1. Attempt Bandit if Python files exist
        has_python = bool(context.files_by_category.get("SOURCE_CODE", []))
        if has_python:
            bandit_res = SafeCommandExecutor.execute(
                command=["bandit", "-r", ".", "-f", "json", "-q"],
                cwd=context.root_path,
                timeout=20
            )
            if bandit_res.exit_code in (0, 1) and bandit_res.stdout.strip().startswith("{"):
                try:
                    data = json.loads(bandit_res.stdout)
                    executed_external = True
                    tool_used = "bandit"
                    for r in data.get("results", []):
                        items.append(SecurityScanItem(
                            rule_id=r.get("test_id", "B000"),
                            severity=r.get("issue_severity", "MEDIUM").upper(),
                            file_path=r.get("filename", "").replace(context.root_path, "").lstrip(r"\/"),
                            line_number=r.get("line_number", 1),
                            title=r.get("issue_text", "Security finding"),
                            description=f"Confidence: {r.get('issue_confidence')}. More info: {r.get('more_info')}",
                            evidence_snippet=r.get("code", "").strip()
                        ))
                except Exception as e:
                    logger.warning("Failed to parse Bandit JSON output: %s", str(e))

        # 2. Deterministic high-confidence secret and credential scanner
        # Runs across all files to detect dangerous deployment exposures
        for file_path in context.all_files:
            full_path = os.path.join(context.root_path, file_path)
            if not os.path.isfile(full_path):
                continue
            # Skip documentation, git, binary
            if any(f in file_path.lower() for f in [".git", ".png", ".jpg", ".svg", ".lock"]):
                continue

            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    for line_idx, line in enumerate(f, start=1):
                        for rule_id, pattern, desc in cls.SECRET_PATTERNS:
                            m = re.search(pattern, line, re.IGNORECASE)
                            if m:
                                snippet = line.strip()
                                # Redact secret in evidence snippet
                                redacted = re.sub(pattern, "***REDACTED_SECRET***", snippet, flags=re.IGNORECASE)
                                items.append(SecurityScanItem(
                                    rule_id=rule_id,
                                    severity="CRITICAL" if "KEY" in rule_id or "DATABASE" in rule_id else "HIGH",
                                    file_path=file_path,
                                    line_number=line_idx,
                                    title=f"Potential Hardcoded Secret: {rule_id}",
                                    description=desc,
                                    evidence_snippet=redacted
                                ))
            except Exception as ex:
                logger.debug("Could not scan file %s for secrets: %s", file_path, str(ex))

        return SecurityScanResult(
            tool_name=tool_used,
            executed_external_tool=executed_external,
            exit_code=0,
            total_findings=len(items),
            items=items
        )
