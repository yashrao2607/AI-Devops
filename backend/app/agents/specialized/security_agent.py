from typing import List
from backend.app.agents.specialized.base import BaseSpecializedAgent
from backend.app.models.analysis_schemas import AnalysisContext, Finding, Evidence
from backend.app.services.tools.security_tools import SecurityTools
from backend.app.core.logging import logger

class SecurityAnalysisAgent(BaseSpecializedAgent):
    """
    Security Analysis Agent (Step 14 of Phase 3).
    Correlates deterministic scanner findings (Bandit, regex secret detectors)
    with repository deployment context, interpreting exposures safely.
    """

    def __init__(self):
        super().__init__(
            agent_name="SecurityAgent",
            prompt_file="security_agent.md"
        )

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        scan_res = SecurityTools.run_security_scan(context)

        for item in scan_res.items:
            severity = item.severity if item.severity in {"CRITICAL", "HIGH", "MEDIUM", "LOW"} else "HIGH"
            findings.append(Finding(
                id=f"F-SEC-{len(findings)+1:03d}",
                category="SECURITY",
                severity=severity,
                confidence="HIGH",
                title=item.title,
                summary=f"Security scanner detected an exposure matching rule {item.rule_id}: {item.description}.",
                impact="Credentials or sensitive data checked into the repository can be compromised during build, image push, or deployment pipelines.",
                recommendation="Extract the secret into an external secret management store or environment variable, and rotate exposed credentials immediately.",
                repository_id=context.repository_id,
                commit_sha=context.commit_sha,
                file_path=item.file_path,
                line_start=item.line_number,
                line_end=item.line_number,
                evidence=item.evidence_snippet,
                evidence_items=[
                    Evidence(
                        evidence_type="SCANNER",
                        file_path=item.file_path,
                        line_start=item.line_number,
                        line_end=item.line_number,
                        snippet=item.evidence_snippet,
                        source=f"scanner:{scan_res.tool_name}",
                        source_tool=scan_res.tool_name,
                        repository_id=context.repository_id
                    )
                ],
                source="deterministic+agent",
                agent="SecurityAgent",
                status="NEW",
                tool_name=scan_res.tool_name,
                rule_id=item.rule_id
            ))

        logger.info("SecurityAgent completed analysis: %d findings identified (tool: %s).",
                    len(findings), scan_res.tool_name)
        return findings
