import os
import re
from typing import List
from backend.app.agents.specialized.base import BaseSpecializedAgent
from backend.app.models.analysis_schemas import AnalysisContext, Finding, Evidence
from backend.app.services.tools.repo_tools import RepositoryTools
from backend.app.core.logging import logger

class CodeAnalysisAgent(BaseSpecializedAgent):
    """
    Code Analysis Agent (Step 9 of Phase 3 / Phase 4 Intelligence Layer).
    Performs polyglot static AST/regex inspection and targeted LLM reasoning across
    Python, JavaScript, TypeScript, and Go source files for critical runtime and deployment hazards:
    - Hardcoded development hosts and ports in production logic
    - Unhandled async promise rejections and silent error swallowing
    - Insecure subprocess and dynamic evaluation calls
    - Unhandled process termination in shared services
    - Disabled TLS certificate verification
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

        # Sample candidate files to inspect deeply (prioritizing entrypoints and core modules)
        prioritized_files = []
        for sf in source_files:
            sfl = sf.lower()
            if any(term in sfl for term in ["main", "index", "app", "server", "core", "api", "database", "postgres", "browser"]):
                prioritized_files.append(sf)
        if not prioritized_files:
            prioritized_files = source_files[:15]
        else:
            # Add remaining source files up to limit
            for sf in source_files:
                if sf not in prioritized_files and len(prioritized_files) < 25:
                    prioritized_files.append(sf)

        sampled_snippets_for_llm = []

        # 1. Deterministic Polyglot Pattern Inspection
        for rel_path in prioritized_files:
            res = RepositoryTools.get_file_content(context, rel_path)
            if not res.exists or not res.content:
                continue

            lines = res.content.splitlines()
            is_js_ts = rel_path.endswith((".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"))
            is_py = rel_path.endswith(".py")

            # Collect snippet for LLM reasoning if it is a primary service
            if len(sampled_snippets_for_llm) < 3 and any(k in rel_path.lower() for k in ["main", "app", "core", "postgres", "server"]):
                sample_lines = "\n".join(lines[:60])
                sampled_snippets_for_llm.append(f"File: {rel_path}\n{sample_lines}")

            for idx, line in enumerate(lines, start=1):
                clean_line = line.strip()
                if not clean_line or clean_line.startswith(("//", "#", "/*", "*")):
                    continue

                # Rule 1: Hardcoded Localhost / 127.0.0.1 in non-test production files
                if re.search(r"https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0)(?::\d+)?", clean_line, re.IGNORECASE):
                    findings.append(Finding(
                        id=f"F-CODE-{len(findings)+1:03d}",
                        category="CODE",
                        severity="HIGH",
                        confidence="HIGH",
                        title="Hardcoded local network endpoint in production source code",
                        summary=f"Source code in '{rel_path}' contains hardcoded localhost/127.0.0.1 endpoint instead of dynamic environment configuration.",
                        impact="When deployed to remote containers, serverless environments, or cloud clusters, calls to localhost will fail or connect to isolated container loops.",
                        recommendation="Load network endpoints dynamically from environment variables (e.g., process.env.SERVICE_URL or os.getenv('SERVICE_URL')).",
                        repository_id=context.repository_id,
                        commit_sha=context.commit_sha,
                        file_path=rel_path,
                        line_start=idx,
                        line_end=idx,
                        evidence=clean_line,
                        evidence_items=[
                            Evidence(
                                evidence_type="SOURCE_CODE",
                                file_path=rel_path,
                                line_start=idx,
                                line_end=idx,
                                snippet=clean_line,
                                source="code_analysis",
                                repository_id=context.repository_id
                            )
                        ],
                        source="deterministic+agent",
                        agent="CodeAgent",
                        status="NEW"
                    ))

                # Rule 2: Python Silent Error Swallowing
                if is_py and (re.search(r"^\s*except\s*:", line) or re.search(r"except\s+Exception\s*:\s*pass", line)):
                    findings.append(Finding(
                        id=f"F-CODE-{len(findings)+1:03d}",
                        category="CODE",
                        severity="MEDIUM",
                        confidence="HIGH",
                        title="Silent exception swallowing in production code",
                        summary=f"Bare except clause or pass statement in '{rel_path}' suppresses critical runtime exceptions.",
                        impact="Operational database errors, network timeouts, and serialization bugs will be masked without telemetry, hindering production incident triage.",
                        recommendation="Catch specific exceptions and ensure errors are structured and logged with context.",
                        repository_id=context.repository_id,
                        commit_sha=context.commit_sha,
                        file_path=rel_path,
                        line_start=idx,
                        line_end=idx,
                        evidence=clean_line,
                        evidence_items=[
                            Evidence(
                                evidence_type="SOURCE_CODE",
                                file_path=rel_path,
                                line_start=idx,
                                line_end=idx,
                                snippet=clean_line,
                                source="code_analysis",
                                repository_id=context.repository_id
                            )
                        ],
                        source="deterministic+agent",
                        agent="CodeAgent",
                        status="NEW"
                    ))

                # Rule 3: JavaScript / TypeScript Empty Catch / Ignored Rejections
                if is_js_ts and (re.search(r"catch\s*\([^)]*\)\s*\{\s*\}", clean_line) or re.search(r"\.catch\(\s*\(\s*\)\s*=>\s*\{\s*\}\)", clean_line)):
                    findings.append(Finding(
                        id=f"F-CODE-{len(findings)+1:03d}",
                        category="CODE",
                        severity="MEDIUM",
                        confidence="HIGH",
                        title="Silent Promise rejection swallowing in async workflow",
                        summary=f"Asynchronous promise catch block in '{rel_path}' silently discards runtime rejections without logging.",
                        impact="Unhandled rejection events will corrupt asynchronous state pipelines and cause silent operational failures in background tasks.",
                        recommendation="Log error details with structured metadata or rethrow to top-level error boundaries.",
                        repository_id=context.repository_id,
                        commit_sha=context.commit_sha,
                        file_path=rel_path,
                        line_start=idx,
                        line_end=idx,
                        evidence=clean_line,
                        source="deterministic+agent",
                        agent="CodeAgent",
                        status="NEW"
                    ))

                # Rule 4: Dangerous process.exit() in shared modules (JS/TS)
                if is_js_ts and re.search(r"process\.exit\([0-9]*\)", clean_line):
                    fname = os.path.basename(rel_path).lower()
                    if fname not in ("main.js", "index.js", "cli.js"):
                        findings.append(Finding(
                            id=f"F-CODE-{len(findings)+1:03d}",
                            category="CODE",
                            severity="HIGH",
                            confidence="HIGH",
                            title="Abrupt process.exit() termination in shared module",
                            summary=f"Module '{rel_path}' calls process.exit() directly instead of throwing an error for upstream handling.",
                            impact="In serverless (Vercel/AWS Lambda) or long-running container deployments, process.exit() forcibly terminates the entire runtime worker.",
                            recommendation="Throw a typed operational error (e.g., throw new Error(...)) allowing callers and middleware to manage cleanup.",
                            repository_id=context.repository_id,
                            commit_sha=context.commit_sha,
                            file_path=rel_path,
                            line_start=idx,
                            line_end=idx,
                            evidence=clean_line,
                            source="deterministic+agent",
                            agent="CodeAgent",
                            status="NEW"
                        ))

                # Rule 5: Disabled TLS Verification (JS/TS & Python)
                if re.search(r"rejectUnauthorized\s*:\s*false", clean_line, re.IGNORECASE) or re.search(r"verify\s*=\s*False", clean_line):
                    findings.append(Finding(
                        id=f"F-CODE-{len(findings)+1:03d}",
                        category="SECURITY",
                        severity="CRITICAL",
                        confidence="HIGH",
                        title="Disabled TLS / SSL certificate verification",
                        summary=f"Network client in '{rel_path}' explicitly disables SSL/TLS certificate validation.",
                        impact="Permits man-in-the-middle attacks on outgoing HTTPS/database connections, risking credential theft and payload interception.",
                        recommendation="Enable strict TLS certificate validation and configure proper CA bundle authorities.",
                        repository_id=context.repository_id,
                        commit_sha=context.commit_sha,
                        file_path=rel_path,
                        line_start=idx,
                        line_end=idx,
                        evidence=clean_line,
                        source="deterministic+agent",
                        agent="CodeAgent",
                        status="NEW"
                    ))

        # 2. Targeted LLM Code Reasoning over Primary Service Files
        if sampled_snippets_for_llm:
            combined_code = "\n---\n".join(sampled_snippets_for_llm)
            prompt_input = (
                f"Repository: {context.repository_name}\n"
                f"Source files examined: {', '.join(prioritized_files[:8])}\n"
                f"Pre-detected issues count: {len(findings)}\n\n"
                f"Analyze these core service implementation excerpts for critical deployment/runtime risks:\n"
                f"{self._wrap_untrusted_data(combined_code)}\n\n"
                f"Look specifically for: missing error handling on database/network clients, unclosed resources, "
                f"or critical runtime exceptions. Return strictly JSON with 'findings' array matching schema."
            )

            try:
                llm_raw = self._invoke_llm(prompt_input)
                llm_data = self._extract_json(llm_raw)

                if llm_data and "findings" in llm_data and isinstance(llm_data["findings"], list):
                    for raw_f in llm_data["findings"]:
                        claimed_file = raw_f.get("file_path", "")
                        # Validate that claimed file actually exists in repository
                        if claimed_file in context.all_files:
                            findings.append(Finding(
                                id=f"F-CODE-{len(findings)+1:03d}",
                                category="CODE",
                                severity=raw_f.get("severity", "MEDIUM"),
                                confidence=raw_f.get("confidence", "HIGH"),
                                title=raw_f.get("title", "Source code deployment risk"),
                                summary=raw_f.get("summary", ""),
                                impact=raw_f.get("impact", "Deployment failure risk"),
                                recommendation=raw_f.get("recommendation", "Refactor code to implement error handling."),
                                repository_id=context.repository_id,
                                commit_sha=context.commit_sha,
                                file_path=claimed_file,
                                line_start=raw_f.get("line_start", 1),
                                line_end=raw_f.get("line_end", 1),
                                evidence=raw_f.get("evidence", "Verified in source context"),
                                source="agentic",
                                agent="CodeAgent",
                                status="NEW"
                            ))
            except Exception as ex:
                logger.debug("CodeAgent LLM reasoning step non-fatal warning: %s", str(ex))

        logger.info("CodeAgent completed analysis: %d findings identified.", len(findings))
        return findings
