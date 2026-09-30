import re
from typing import List
from backend.app.agents.specialized.base import BaseSpecializedAgent
from backend.app.models.analysis_schemas import AnalysisContext, Finding, Evidence
from backend.app.services.tools.repo_tools import RepositoryTools
from backend.app.core.logging import logger

class CodeAnalysisAgent(BaseSpecializedAgent):
    """
    Code Analysis Agent (Step 9 of Phase 3).
    Inspects source code for deployment risks:
    - Hardcoded development hosts and ports in production logic
    - Unhandled exceptions in network/database transactions
    - Hazardous execution patterns
    """

    def __init__(self):
        super().__init__(
            agent_name="CodeAgent",
            prompt_file="code_agent.md"
        )

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        source_files = context.files_by_category.get("SOURCE_CODE", [])
        if not source_files:
            return findings

        # 1. Deterministic code inspection for deployment-sensitive risks
        for rel_path in source_files:
            res = RepositoryTools.get_file_content(context, rel_path)
            if not res.exists or not res.content:
                continue

            for idx, line in enumerate(res.content.splitlines(), start=1):
                # Pattern A: Hardcoded localhost or internal IP in production code
                if re.search(r"https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0)", line, re.IGNORECASE):
                    findings.append(Finding(
                        id=f"F-CODE-{len(findings)+1:03d}",
                        category="CODE",
                        severity="HIGH",
                        confidence="HIGH",
                        title="Hardcoded local network endpoint in source code",
                        summary="Source code contains a hardcoded localhost/127.0.0.1 URI instead of using environment configuration.",
                        impact="Application will fail to communicate with remote services when deployed to container or cloud staging/production environments.",
                        recommendation="Replace hardcoded URL with an environment variable (e.g., os.getenv('SERVICE_URL')).",
                        repository_id=context.repository_id,
                        commit_sha=context.commit_sha,
                        file_path=rel_path,
                        line_start=idx,
                        line_end=idx,
                        evidence=line.strip(),
                        evidence_items=[
                            Evidence(
                                evidence_type="SOURCE_CODE",
                                file_path=rel_path,
                                line_start=idx,
                                line_end=idx,
                                snippet=line.strip(),
                                source="code_analysis",
                                repository_id=context.repository_id
                            )
                        ],
                        source="deterministic+agent",
                        agent="CodeAgent",
                        status="NEW"
                    ))

                # Pattern B: Bare except / silently swallowed exceptions
                if re.search(r"^\s*except\s*:", line) or re.search(r"except\s+Exception:\s*pass", line):
                    findings.append(Finding(
                        id=f"F-CODE-{len(findings)+1:03d}",
                        category="CODE",
                        severity="MEDIUM",
                        confidence="HIGH",
                        title="Silent exception swallowing in operational code",
                        summary="A bare except clause or pass statement silences critical runtime errors.",
                        impact="Operational failures and database timeouts will be masked in production logs, impeding incident diagnosis.",
                        recommendation="Catch specific exceptions and ensure proper structured logging of the stack trace.",
                        repository_id=context.repository_id,
                        commit_sha=context.commit_sha,
                        file_path=rel_path,
                        line_start=idx,
                        line_end=idx,
                        evidence=line.strip(),
                        evidence_items=[
                            Evidence(
                                evidence_type="SOURCE_CODE",
                                file_path=rel_path,
                                line_start=idx,
                                line_end=idx,
                                snippet=line.strip(),
                                source="code_analysis",
                                repository_id=context.repository_id
                            )
                        ],
                        source="deterministic+agent",
                        agent="CodeAgent",
                        status="NEW"
                    ))

        # 2. LLM reasoning over gathered source context
        prompt_input = (
            f"Repository: {context.repository_name}\n"
            f"Source files: {', '.join(source_files[:10])}\n"
            f"Pre-detected issues count: {len(findings)}\n"
            f"{self._wrap_untrusted_data('Source file analysis completed.')}"
        )

        llm_raw = self._invoke_llm(prompt_input)
        llm_data = self._extract_json(llm_raw)

        if llm_data and "findings" in llm_data and isinstance(llm_data["findings"], list):
            for raw_f in llm_data["findings"]:
                # Verify that claimed file actually exists in repository
                claimed_file = raw_f.get("file_path", "")
                if claimed_file in context.all_files:
                    findings.append(Finding(
                        id=f"F-CODE-{len(findings)+1:03d}",
                        category="CODE",
                        severity=raw_f.get("severity", "MEDIUM"),
                        confidence=raw_f.get("confidence", "MEDIUM"),
                        title=raw_f.get("title", "Source code risk"),
                        summary=raw_f.get("summary", ""),
                        impact=raw_f.get("impact", "Deployment failure risk"),
                        recommendation=raw_f.get("recommendation", "Refactor code"),
                        repository_id=context.repository_id,
                        commit_sha=context.commit_sha,
                        file_path=claimed_file,
                        line_start=raw_f.get("line_start"),
                        line_end=raw_f.get("line_end"),
                        evidence=raw_f.get("evidence", ""),
                        source="agentic",
                        agent="CodeAgent",
                        status="NEW"
                    ))

        logger.info("CodeAgent completed analysis: %d findings identified.", len(findings))
        return findings
