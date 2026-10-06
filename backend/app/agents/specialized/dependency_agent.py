import os
import re
import json
from typing import List
from backend.app.agents.specialized.base import BaseSpecializedAgent
from backend.app.models.analysis_schemas import AnalysisContext, Finding, Evidence
from backend.app.services.tools.repo_tools import RepositoryTools
from backend.app.core.logging import logger

class DependencyAnalysisAgent(BaseSpecializedAgent):
    """
    Dependency Analysis Agent (Step 10 of Phase 3 / Phase 4 Intelligence Layer).
    Inspects package manifests (requirements.txt, package.json, pyproject.toml, Pipfile)
    for supply-chain risks, unpinned dependencies, missing lockfiles, and deprecated packages.
    """

    DEPRECATED_PACKAGES = {
        "request": "The 'request' library has been officially deprecated since 2020 and contains unpatched vulnerabilities.",
        "node-uuid": "The 'node-uuid' package is deprecated. Use the official 'uuid' package instead.",
        "left-pad": "The 'left-pad' package is unmaintained and represents supply-chain technical debt.",
        "querystring": "The npm 'querystring' package is legacy; use native URLSearchParams in modern Node.js.",
    }

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
            # 1. Python requirements.txt / Pipfile
            if m.manifest_type == "python_pip" or m.file_path.endswith("requirements.txt"):
                lines = m.raw_content.splitlines()
                for idx, line in enumerate(lines, start=1):
                    clean_line = line.strip()
                    if not clean_line or clean_line.startswith("#") or clean_line.startswith("-"):
                        continue

                    # Unpinned pattern: package name with no version constraint or wildcard
                    if not re.search(r"[=><~]", clean_line) or clean_line.endswith("*") or "latest" in clean_line:
                        pkg_name = clean_line.split()[0] if clean_line.split() else clean_line
                        findings.append(Finding(
                            id=f"F-DEP-{len(findings)+1:03d}",
                            category="DEPENDENCY",
                            severity="HIGH",
                            confidence="HIGH",
                            title=f"Unpinned dependency in manifest: '{pkg_name}'",
                            summary=f"Package '{pkg_name}' is declared without an explicit version pin in {m.file_path}.",
                            impact="CI/CD and container builds will fetch the latest upstream release arbitrarily, causing breaking changes and deployment outages.",
                            recommendation=f"Pin the exact tested version (e.g., '{pkg_name}==x.y.z') and maintain an immutable lockfile.",
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

            # 2. Node.js package.json
            if m.manifest_type == "nodejs_npm" or m.file_path.endswith("package.json"):
                # Check for lockfile
                has_lock = any(
                    "package-lock.json" in f or "yarn.lock" in f or "pnpm-lock.yaml" in f
                    for f in context.all_files
                )
                if not has_lock:
                    findings.append(Finding(
                        id=f"F-DEP-{len(findings)+1:03d}",
                        category="DEPENDENCY",
                        severity="MEDIUM",
                        confidence="HIGH",
                        title="Missing npm / yarn lockfile in repository",
                        summary="package.json is present but no lockfile (package-lock.json or yarn.lock) was detected.",
                        impact="Non-deterministic npm dependency resolutions can produce divergent production container builds between environments.",
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

                # Parse JSON to inspect dependencies
                try:
                    pkg_data = json.loads(m.raw_content)
                    deps = pkg_data.get("dependencies", {})
                    
                    for pkg_name, ver in deps.items():
                        ver_str = str(ver).strip()
                        # Check wildcard or latest
                        if ver_str in ("*", "latest") or ver_str.startswith("latest"):
                            findings.append(Finding(
                                id=f"F-DEP-{len(findings)+1:03d}",
                                category="DEPENDENCY",
                                severity="HIGH",
                                confidence="HIGH",
                                title=f"Wildcard / latest dependency version: '{pkg_name}'",
                                summary=f"Production dependency '{pkg_name}' uses wildcard version specifier '{ver_str}' in {m.file_path}.",
                                impact="Deployment pipelines will pull arbitrary new major releases at build time, guaranteeing unexpected production breakage.",
                                recommendation=f"Specify an exact or bounded semver range for '{pkg_name}'.",
                                repository_id=context.repository_id,
                                commit_sha=context.commit_sha,
                                file_path=m.file_path,
                                line_start=1,
                                line_end=1,
                                evidence=f'"{pkg_name}": "{ver_str}"',
                                source="deterministic+agent",
                                agent="DependencyAgent",
                                status="NEW"
                            ))

                        # Check deprecated packages
                        if pkg_name.lower() in cls.DEPRECATED_PACKAGES:
                            reason = cls.DEPRECATED_PACKAGES[pkg_name.lower()]
                            findings.append(Finding(
                                id=f"F-DEP-{len(findings)+1:03d}",
                                category="DEPENDENCY",
                                severity="HIGH",
                                confidence="HIGH",
                                title=f"Deprecated production dependency: '{pkg_name}'",
                                summary=f"Package '{pkg_name}' is deprecated: {reason}",
                                impact="Deprecated dependencies receive zero security patches and introduce unmonitored CVE attack vectors.",
                                recommendation=f"Migrate away from '{pkg_name}' to a supported modern alternative.",
                                repository_id=context.repository_id,
                                commit_sha=context.commit_sha,
                                file_path=m.file_path,
                                line_start=1,
                                line_end=1,
                                evidence=f'"{pkg_name}": "{ver_str}"',
                                source="deterministic+agent",
                                agent="DependencyAgent",
                                status="NEW"
                            ))
                except Exception as ex:
                    logger.debug("Could not parse package.json for dependency checks: %s", str(ex))

        # 3. LLM Supply-Chain Reasoning over manifests
        if manifests:
            manifest_summary = "\n\n".join([f"Manifest ({m.file_path}):\n{m.raw_content[:800]}" for m in manifests[:2]])
            prompt_input = (
                f"Repository: {context.repository_name}\n"
                f"Review these package manifests for deployment supply chain risks:\n"
                f"{self._wrap_untrusted_data(manifest_summary)}\n\n"
                f"Identify any conflicting versions, outdated major frameworks, or dangerous supply-chain exposures. "
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
                                id=f"F-DEP-{len(findings)+1:03d}",
                                category="DEPENDENCY",
                                severity=raw_f.get("severity", "MEDIUM"),
                                confidence=raw_f.get("confidence", "HIGH"),
                                title=raw_f.get("title", "Supply chain dependency risk"),
                                summary=raw_f.get("summary", ""),
                                impact=raw_f.get("impact", "Supply chain deployment risk"),
                                recommendation=raw_f.get("recommendation", "Update dependency configuration."),
                                repository_id=context.repository_id,
                                commit_sha=context.commit_sha,
                                file_path=claimed_file,
                                line_start=raw_f.get("line_start", 1),
                                line_end=raw_f.get("line_end", 1),
                                evidence=raw_f.get("evidence", "Verified in package manifest"),
                                source="agentic",
                                agent="DependencyAgent",
                                status="NEW"
                            ))
            except Exception as ex:
                logger.debug("DependencyAgent LLM reasoning step non-fatal warning: %s", str(ex))

        logger.info("DependencyAgent completed analysis: %d findings identified.", len(findings))
        return findings
