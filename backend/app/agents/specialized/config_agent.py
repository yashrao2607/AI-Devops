import os
import re
from typing import List
from backend.app.agents.specialized.base import BaseSpecializedAgent
from backend.app.models.analysis_schemas import AnalysisContext, Finding, Evidence
from backend.app.services.tools.repo_tools import RepositoryTools
from backend.app.core.logging import logger

class ConfigurationAnalysisAgent(BaseSpecializedAgent):
    """
    Configuration & Containerization Agent (Step 11 of Phase 3 / Phase 4 Intelligence Layer).
    Analyzes Dockerfile, docker-compose.yml, CI/CD workflows (.github/workflows),
    Vercel/Netlify configs, and cloud manifests for deployment, container, and infrastructure hazards.
    """

    def __init__(self):
        super().__init__(
            agent_name="ConfigAgent",
            prompt_file="config_agent.md"
        )

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        config_files = (
            context.files_by_category.get("CONFIG", []) +
            context.files_by_category.get("DOCKER", []) +
            context.files_by_category.get("CI_CD", [])
        )

        # Also discover any workflow files or deploy files in repo
        for f in context.all_files:
            if f not in config_files and any(term in f.lower() for term in [".github/workflows", "vercel.json", "compose", "dockerfile", "k8s"]):
                config_files.append(f)

        sampled_config_for_llm = []

        for rel_path in config_files:
            res = RepositoryTools.get_file_content(context, rel_path)
            if not res.exists or not res.content:
                continue

            lines = res.content.splitlines()
            lower_path = rel_path.lower()

            if len(sampled_config_for_llm) < 3 and any(k in lower_path for k in ["workflow", "dockerfile", "vercel", "compose"]):
                sampled_config_for_llm.append(f"File: {rel_path}\n{res.content[:800]}")

            # -------------------------------------------------------------
            # 1. Dockerfile checks
            # -------------------------------------------------------------
            if "dockerfile" in lower_path:
                has_user_directive = False
                for idx, line in enumerate(lines, start=1):
                    clean_line = line.strip()
                    if clean_line.upper().startswith("USER "):
                        has_user_directive = True

                    # Check unpinned base image (e.g. FROM python:latest or FROM python)
                    if clean_line.upper().startswith("FROM "):
                        image_part = clean_line.split()[1] if len(clean_line.split()) > 1 else ""
                        if ":latest" in image_part or ":" not in image_part:
                            findings.append(Finding(
                                id=f"F-CFG-{len(findings)+1:03d}",
                                category="CONTAINERIZATION",
                                severity="HIGH",
                                confidence="HIGH",
                                title=f"Unpinned base container image tag: '{image_part}'",
                                summary=f"Dockerfile uses an unpinned or ':latest' container image tag ({image_part}).",
                                impact="Upstream base image updates may silently alter system libraries, breaking production container builds unpredictably.",
                                recommendation="Pin the base image to an exact immutable version tag or SHA256 digest.",
                                repository_id=context.repository_id,
                                commit_sha=context.commit_sha,
                                file_path=rel_path,
                                line_start=idx,
                                line_end=idx,
                                evidence=clean_line,
                                evidence_items=[
                                    Evidence(
                                        evidence_type="CONFIGURATION",
                                        file_path=rel_path,
                                        line_start=idx,
                                        line_end=idx,
                                        snippet=clean_line,
                                        source="dockerfile_check",
                                        repository_id=context.repository_id
                                    )
                                ],
                                source="deterministic+agent",
                                agent="ConfigAgent",
                                status="NEW"
                            ))

                    # Check for secrets in ENV instructions
                    if clean_line.upper().startswith("ENV ") and re.search(r"(?:KEY|SECRET|PASSWORD|TOKEN)\s*=", clean_line, re.IGNORECASE):
                        findings.append(Finding(
                            id=f"F-CFG-{len(findings)+1:03d}",
                            category="SECURITY",
                            severity="CRITICAL",
                            confidence="HIGH",
                            title="Sensitive credential declared in Dockerfile ENV instruction",
                            summary="Dockerfile declares a sensitive key or password directly inside an ENV layer.",
                            impact="ENV values are permanently baked into exported container image metadata and visible to anyone with image pull rights.",
                            recommendation="Pass sensitive parameters at runtime using secrets managers or container orchestrator environment mounts.",
                            repository_id=context.repository_id,
                            commit_sha=context.commit_sha,
                            file_path=rel_path,
                            line_start=idx,
                            line_end=idx,
                            evidence=clean_line,
                            source="deterministic+agent",
                            agent="ConfigAgent",
                            status="NEW"
                        ))

                if not has_user_directive and len(lines) > 5:
                    findings.append(Finding(
                        id=f"F-CFG-{len(findings)+1:03d}",
                        category="CONTAINERIZATION",
                        severity="MEDIUM",
                        confidence="HIGH",
                        title="Missing non-root USER instruction in Dockerfile",
                        summary="Dockerfile executes container processes under default root user.",
                        impact="Container breakout vulnerabilities allow compromised web applications to access the host operating system with root privileges.",
                        recommendation="Define an unprivileged user (e.g., USER node or USER appuser) before entrypoint execution.",
                        repository_id=context.repository_id,
                        commit_sha=context.commit_sha,
                        file_path=rel_path,
                        line_start=1,
                        line_end=1,
                        evidence="No USER directive detected in Dockerfile.",
                        source="deterministic",
                        agent="ConfigAgent",
                        status="NEW"
                    ))

            # -------------------------------------------------------------
            # 2. CI/CD Workflows (.github/workflows)
            # -------------------------------------------------------------
            if ".github/workflows" in lower_path or lower_path.endswith((".yml", ".yaml")):
                has_timeout = False
                for idx, line in enumerate(lines, start=1):
                    clean_line = line.strip()
                    if "timeout-minutes:" in clean_line:
                        has_timeout = True

                    # Legacy unpinned GitHub action (e.g. actions/checkout@v2 or actions/setup-node@v2)
                    m_action = re.search(r"uses:\s*([a-zA-Z0-9_\-\/]+)@(v[123])\b", clean_line)
                    if m_action:
                        action_name = m_action.group(1)
                        version_tag = m_action.group(2)
                        findings.append(Finding(
                            id=f"F-CFG-{len(findings)+1:03d}",
                            category="CI_CD",
                            severity="HIGH",
                            confidence="HIGH",
                            title=f"Deprecated GitHub Action version in CI/CD: '{action_name}@{version_tag}'",
                            summary=f"Workflow '{rel_path}' uses deprecated action '{action_name}@{version_tag}' which relies on obsolete Node runtimes.",
                            impact="GitHub Actions runners deprecate legacy action versions, causing pipeline failures or unexpected execution errors.",
                            recommendation=f"Upgrade action to modern version (e.g., '{action_name}@v4') or pin to immutable commit SHA.",
                            repository_id=context.repository_id,
                            commit_sha=context.commit_sha,
                            file_path=rel_path,
                            line_start=idx,
                            line_end=idx,
                            evidence=clean_line,
                            source="deterministic+agent",
                            agent="ConfigAgent",
                            status="NEW"
                        ))

            # -------------------------------------------------------------
            # 3. Docker Compose & Environment checks
            # -------------------------------------------------------------
            if "compose" in lower_path:
                for idx, line in enumerate(lines, start=1):
                    clean_line = line.strip()
                    if re.search(r"DEBUG\s*[:=]\s*['\"]?(?:true|1)['\"]?", clean_line, re.IGNORECASE):
                        findings.append(Finding(
                            id=f"F-CFG-{len(findings)+1:03d}",
                            category="ENVIRONMENT",
                            severity="HIGH",
                            confidence="HIGH",
                            title="Debug mode enabled in compose container deployment",
                            summary="Container compose specification sets DEBUG=True or DEBUG=1.",
                            impact="Running debug mode in deployed containers leaks internal stack traces and disables performance optimizations.",
                            recommendation="Set DEBUG=False for all deployment containers.",
                            repository_id=context.repository_id,
                            commit_sha=context.commit_sha,
                            file_path=rel_path,
                            line_start=idx,
                            line_end=idx,
                            evidence=clean_line,
                            source="deterministic+agent",
                            agent="ConfigAgent",
                            status="NEW"
                        ))

                    # Database ports publicly bound
                    if re.search(r"['\"]?0\.0\.0\.0:(?:5432|3306|27017|6379):", clean_line):
                        findings.append(Finding(
                            id=f"F-CFG-{len(findings)+1:03d}",
                            category="SECURITY",
                            severity="CRITICAL",
                            confidence="HIGH",
                            title="Database port exposed to public network interface (0.0.0.0)",
                            summary="Database service port is mapped directly to 0.0.0.0 on the host interface.",
                            impact="Exposes the database directly to external network scanners and internet traffic, risking unauthorized database penetration.",
                            recommendation="Bind database ports to internal Docker network or restrict to 127.0.0.1:port.",
                            repository_id=context.repository_id,
                            commit_sha=context.commit_sha,
                            file_path=rel_path,
                            line_start=idx,
                            line_end=idx,
                            evidence=clean_line,
                            source="deterministic+agent",
                            agent="ConfigAgent",
                            status="NEW"
                        ))

        # 4. LLM Configuration Reasoning
        if sampled_config_for_llm:
            combined_cfg = "\n---\n".join(sampled_config_for_llm)
            prompt_input = (
                f"Repository: {context.repository_name}\n"
                f"Review these deployment and CI/CD configuration files for deployment and infrastructure risks:\n"
                f"{self._wrap_untrusted_data(combined_cfg)}\n\n"
                f"Identify any missing health checks, dangerous secrets, misconfigured build commands, or cloud deployment gaps. "
                f"Return strictly JSON with 'findings' array matching schema."
            )
            try:
                llm_raw = self._invoke_llm(prompt_input)
                llm_data = self._extract_json(llm_raw)
                if llm_data and "findings" in llm_data and isinstance(llm_data["findings"], list):
                    for raw_f in llm_data["findings"]:
                        claimed_file = raw_f.get("file_path", "")
                        if claimed_file in context.all_files:
                            findings.append(Finding(
                                id=f"F-CFG-{len(findings)+1:03d}",
                                category="CONFIGURATION",
                                severity=raw_f.get("severity", "MEDIUM"),
                                confidence=raw_f.get("confidence", "HIGH"),
                                title=raw_f.get("title", "Infrastructure configuration risk"),
                                summary=raw_f.get("summary", ""),
                                impact=raw_f.get("impact", "Deployment infrastructure hazard"),
                                recommendation=raw_f.get("recommendation", "Update deployment configuration."),
                                repository_id=context.repository_id,
                                commit_sha=context.commit_sha,
                                file_path=claimed_file,
                                line_start=raw_f.get("line_start", 1),
                                line_end=raw_f.get("line_end", 1),
                                evidence=raw_f.get("evidence", "Verified in configuration file"),
                                source="agentic",
                                agent="ConfigAgent",
                                status="NEW"
                            ))
            except Exception as ex:
                logger.debug("ConfigAgent LLM reasoning step non-fatal warning: %s", str(ex))

        logger.info("ConfigAgent completed analysis: %d findings identified.", len(findings))
        return findings
