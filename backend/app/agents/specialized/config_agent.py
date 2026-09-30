import os
import re
from typing import List
from backend.app.agents.specialized.base import BaseSpecializedAgent
from backend.app.models.analysis_schemas import AnalysisContext, Finding, Evidence
from backend.app.services.tools.repo_tools import RepositoryTools
from backend.app.core.logging import logger

class ConfigurationAnalysisAgent(BaseSpecializedAgent):
    """
    Configuration Agent (Step 11 of Phase 3).
    Inspects Dockerfile, docker-compose.yml, environment manifests,
    and CI/CD workflows for operational deployment and containerization hazards.
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

        for rel_path in config_files:
            res = RepositoryTools.get_file_content(context, rel_path)
            if not res.exists or not res.content:
                continue

            lines = res.content.splitlines()

            # 1. Dockerfile checks
            if "dockerfile" in rel_path.lower():
                for idx, line in enumerate(lines, start=1):
                    # Check unpinned base image (e.g. FROM python:latest or FROM python)
                    if line.strip().upper().startswith("FROM "):
                        image_part = line.strip().split()[1] if len(line.strip().split()) > 1 else ""
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
                                evidence=line.strip(),
                                evidence_items=[
                                    Evidence(
                                        evidence_type="CONFIGURATION",
                                        file_path=rel_path,
                                        line_start=idx,
                                        line_end=idx,
                                        snippet=line.strip(),
                                        source="dockerfile_check",
                                        repository_id=context.repository_id
                                    )
                                ],
                                source="deterministic+agent",
                                agent="ConfigAgent",
                                status="NEW"
                            ))

            # 2. Hardcoded production database configuration
            if any(term in rel_path.lower() for term in ["prod", "production", "config.py", "database.py"]):
                for idx, line in enumerate(lines, start=1):
                    if re.search(r"DATABASE_URI\s*=\s*['\"]postgres://[^'\"]+['\"]", line, re.IGNORECASE):
                        findings.append(Finding(
                            id=f"F-CFG-{len(findings)+1:03d}",
                            category="CONFIGURATION",
                            severity="CRITICAL",
                            confidence="HIGH",
                            title="Hardcoded production database connection string",
                            summary="Production configuration file specifies a static database connection URI directly in source code.",
                            impact="Credentials will be committed to VCS and production database cannot be dynamically configured across environments.",
                            recommendation="Load database connection strings dynamically using os.environ.get('DATABASE_URL').",
                            repository_id=context.repository_id,
                            commit_sha=context.commit_sha,
                            file_path=rel_path,
                            line_start=idx,
                            line_end=idx,
                            evidence=line.strip(),
                            evidence_items=[
                                Evidence(
                                    evidence_type="CONFIGURATION",
                                    file_path=rel_path,
                                    line_start=idx,
                                    line_end=idx,
                                    snippet=line.strip(),
                                    source="config_check",
                                    repository_id=context.repository_id
                                )
                            ],
                            source="deterministic+agent",
                            agent="ConfigAgent",
                            status="NEW"
                        ))

            # 3. Docker Compose environment check
            if "docker-compose" in rel_path.lower():
                has_env_file = any(".env" in f for f in context.all_files)
                # Check for debug mode enabled in compose
                for idx, line in enumerate(lines, start=1):
                    if re.search(r"DEBUG\s*[:=]\s*['\"]?(?:true|1)['\"]?", line, re.IGNORECASE):
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
                            evidence=line.strip(),
                            source="deterministic+agent",
                            agent="ConfigAgent",
                            status="NEW"
                        ))

        logger.info("ConfigAgent completed analysis: %d findings identified.", len(findings))
        return findings
