import os
import re
from typing import List
from backend.app.agents.specialized.base import BaseSpecializedAgent
from backend.app.models.analysis_schemas import AnalysisContext, Finding, Evidence
from backend.app.services.tools.repo_tools import RepositoryTools
from backend.app.core.logging import logger

class DependencyAnalysisAgent(BaseSpecializedAgent):
    """
    Dependency Analysis Agent (Step 10 of Phase 3).
    Inspects package manifests (requirements.txt, package.json, pyproject.toml)
    for unpinned libraries, conflict hazards, and supply-chain deployment risks.
    """

    def __init__(self):
        super().__init__(
            agent_name="DependencyAgent",
            prompt_file="dependency_agent.md"
        )

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        manifests = RepositoryTools.get_dependency_manifests(context)

        if not manifests:
            logger.info("DependencyAgent: No package manifests found in repository.")
            return findings

        for m in manifests:
            # Check requirements.txt for unpinned packages
            if m.manifest_type == "python_pip":
                lines = m.raw_content.splitlines()
                for idx, line in enumerate(lines, start=1):
                    clean_line = line.strip()
                    if not clean_line or clean_line.startswith("#") or clean_line.startswith("-"):
                        continue

                    # Unpinned pattern: package name with no version constraint or wildcard
                    if not re.search(r"[=><~]", clean_line) or clean_line.endswith("*"):
                        pkg_name = clean_line.split()[0]
                        findings.append(Finding(
                            id=f"F-DEP-{len(findings)+1:03d}",
                            category="DEPENDENCY",
                            severity="HIGH",
                            confidence="HIGH",
                            title=f"Unpinned dependency in manifest: '{pkg_name}'",
                            summary=f"Package '{pkg_name}' is declared without an explicit version pin in {m.file_path}.",
                            impact="Builds in CI/CD will fetch the latest upstream release arbitrarily, risking sudden deployment outages due to breaking changes.",
                            recommendation=f"Pin the exact tested version (e.g., '{pkg_name}==x.y.z') and maintain a lockfile.",
                            repository_id=context.repository_id,
                            commit_sha=context.commit_sha,
                            file_path=m.file_path,
                            line_start=idx,
                            line_end=idx,
                            evidence=clean_line,
                            evidence_items=[
                                Evidence(
                                    evidence_type="DEPENDENCY_MANIFEST",
                                    file_path=m.file_path,
                                    line_start=idx,
                                    line_end=idx,
                                    snippet=clean_line,
                                    source="dependency_manifest",
                                    repository_id=context.repository_id
                                )
                            ],
                            source="deterministic+agent",
                            agent="DependencyAgent",
                            status="NEW"
                        ))

            # Check for missing lockfile in Python/Node projects
            if m.manifest_type == "nodejs_npm":
                has_lock = any("package-lock.json" in f or "yarn.lock" in f for f in context.all_files)
                if not has_lock:
                    findings.append(Finding(
                        id=f"F-DEP-{len(findings)+1:03d}",
                        category="DEPENDENCY",
                        severity="MEDIUM",
                        confidence="HIGH",
                        title="Missing npm lockfile in repository",
                        summary="package.json is present but package-lock.json / yarn.lock was not detected.",
                        impact="Non-deterministic npm dependency resolutions can produce divergent production container builds.",
                        recommendation="Run 'npm install' locally and commit 'package-lock.json' to version control.",
                        repository_id=context.repository_id,
                        commit_sha=context.commit_sha,
                        file_path=m.file_path,
                        line_start=1,
                        line_end=1,
                        evidence="package.json detected without corresponding lockfile.",
                        source="deterministic",
                        agent="DependencyAgent",
                        status="NEW"
                    ))

        logger.info("DependencyAgent completed analysis: %d findings identified.", len(findings))
        return findings
