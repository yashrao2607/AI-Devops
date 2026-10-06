import os
import json
import re
from typing import List
from backend.app.agents.specialized.base import BaseSpecializedAgent
from backend.app.models.analysis_schemas import AnalysisContext, Finding, Evidence
from backend.app.services.tools.repo_tools import RepositoryTools
from backend.app.services.tools.test_tools import TestTools
from backend.app.core.logging import logger

class TestAnalysisAgent(BaseSpecializedAgent):
    """
    Test Analysis Agent (Step 12 of Phase 3 / Phase 4 Intelligence Layer).
    Strictly distinguishes between:
    - OBSERVED: Executed automated test suite failures from safe test runners
    - INFERRED: Missing unit or regression test suites for core business services
    - CONFIGURATION: Dummy or unconfigured test scripts in package manifests
    """
    __test__ = False

    def __init__(self):
        super().__init__(
            agent_name="TestAgent",
            prompt_file="test_agent.md"
        )

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        test_files = RepositoryTools.get_test_files(context)
        source_files = context.files_by_category.get("SOURCE_CODE", [])

        # 1. Check for npm dummy test script in package.json
        for f in context.all_files:
            if f.endswith("package.json"):
                pkg_res = RepositoryTools.get_file_content(context, f)
                if pkg_res.exists and pkg_res.content:
                    try:
                        pkg_data = json.loads(pkg_res.content)
                        test_script = pkg_data.get("scripts", {}).get("test", "")
                        if "no test specified" in test_script or test_script.strip() == "exit 1":
                            findings.append(Finding(
                                id=f"F-TST-{len(findings)+1:03d}",
                                category="TEST",
                                severity="HIGH",
                                confidence="HIGH",
                                title="Default unconfigured 'echo no test specified' script in package.json",
                                summary="package.json contains npm's placeholder test script that exits with code 1.",
                                impact="Standard CI/CD test phases will automatically fail build pipelines when executing 'npm test'.",
                                recommendation="Configure a valid test runner (e.g. jest, vitest, or node --test) or adjust CI script target.",
                                repository_id=context.repository_id,
                                commit_sha=context.commit_sha,
                                file_path=f,
                                line_start=1,
                                line_end=1,
                                evidence=f'"test": "{test_script}"',
                                source="deterministic",
                                agent="TestAgent",
                                status="NEW"
                            ))
                    except Exception:
                        pass

        # 2. OBSERVED test execution if safe execution is permitted
        if test_files:
            test_run = TestTools.run_tests_safe(context)
            if test_run.executed and test_run.tests_failed > 0:
                findings.append(Finding(
                    id=f"F-TST-{len(findings)+1:03d}",
                    category="TEST",
                    severity="CRITICAL",
                    confidence="HIGH",
                    title=f"OBSERVED: {test_run.tests_failed} automated test(s) failed in repository",
                    summary=f"Automated test suite executed with exit code {test_run.exit_code}. {test_run.summary_message}",
                    impact="Deploying with failing unit/regression tests introduces proven defects directly into production.",
                    recommendation="Fix all failing unit test assertions prior to deployment approval.",
                    repository_id=context.repository_id,
                    commit_sha=context.commit_sha,
                    file_path=test_files[0],
                    line_start=1,
                    line_end=1,
                    evidence=test_run.raw_output[:500],
                    evidence_items=[
                        Evidence(
                            evidence_type="TEST_RESULT",
                            file_path=test_files[0],
                            snippet=test_run.raw_output[:300],
                            source="test_runner",
                            repository_id=context.repository_id
                        )
                    ],
                    source="deterministic",
                    agent="TestAgent",
                    status="NEW"
                ))

        # 3. INFERRED: Check for missing regression tests in core modules
        critical_domains = ["postgres", "database", "payment", "billing", "auth", "checkout", "security", "crypto", "browser"]
        for src_path in source_files:
            fname = os.path.basename(src_path).lower()
            for domain in critical_domains:
                if domain in fname:
                    # Check if any test file corresponds to this critical module
                    has_matching_test = any(domain in t.lower() for t in test_files)
                    if not has_matching_test:
                        findings.append(Finding(
                            id=f"F-TST-{len(findings)+1:03d}",
                            category="TEST",
                            severity="HIGH",
                            confidence="MEDIUM",
                            title=f"INFERRED: Missing regression tests for critical '{domain}' service",
                            summary=f"Critical business logic module '{src_path}' has no corresponding test file in the test suite.",
                            impact="Changes to core persistence or operational logic lack automated verification, risking silent data corruption or deployment crashes.",
                            recommendation=f"Author automated unit tests (e.g. tests/{domain}.test.js or test_{domain}.py) covering happy path and edge cases.",
                            repository_id=context.repository_id,
                            commit_sha=context.commit_sha,
                            file_path=src_path,
                            line_start=1,
                            line_end=20,
                            evidence=f"Discovered critical module '{src_path}' without matching test in {len(test_files)} discovered test files.",
                            source="agentic",
                            agent="TestAgent",
                            status="NEW"
                        ))

        # 4. If zero test files exist in entire repository
        if not test_files and source_files:
            findings.append(Finding(
                id=f"F-TST-{len(findings)+1:03d}",
                category="TEST",
                severity="HIGH",
                confidence="HIGH",
                title="INFERRED: Zero automated test files discovered in repository",
                summary="The repository contains production source code but zero unit or integration test files.",
                impact="Unverified releases lack automated safety nets against regressions and runtime crashes.",
                recommendation="Introduce a standard test runner (e.g., pytest or jest) with baseline sanity test coverage.",
                repository_id=context.repository_id,
                commit_sha=context.commit_sha,
                file_path=source_files[0],
                line_start=1,
                line_end=1,
                evidence="Zero files discovered matching test categories or naming patterns.",
                source="deterministic+agent",
                agent="TestAgent",
                status="NEW"
            ))

        logger.info("TestAgent completed analysis: %d findings identified.", len(findings))
        return findings
