import os
from typing import List
from backend.app.agents.specialized.base import BaseSpecializedAgent
from backend.app.models.analysis_schemas import AnalysisContext, Finding, Evidence
from backend.app.services.tools.repo_tools import RepositoryTools
from backend.app.services.tools.test_tools import TestTools
from backend.app.core.logging import logger

class TestAnalysisAgent(BaseSpecializedAgent):
    """
    Test Analysis Agent (Step 12 of Phase 3).
    Strictly distinguishes between:
    - OBSERVED: Executed test failures from safe test runners
    - INFERRED: Missing unit or regression tests for critical source modules
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

        # 1. OBSERVED test execution if safe execution is permitted
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
                            source="pytest_runner",
                            repository_id=context.repository_id
                        )
                    ],
                    source="deterministic",
                    agent="TestAgent",
                    status="NEW"
                ))

        # 2. INFERRED check for missing regression tests in critical domains
        critical_domains = ["payment", "billing", "auth", "checkout", "security", "crypto"]
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
                            impact="Changes to core revenue/security logic lack automated regression verification, increasing production incident probability.",
                            recommendation=f"Author automated unit tests (e.g. tests/test_{domain}.py) covering happy path and edge cases.",
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

        # If zero test files exist in entire repository
        if not test_files and source_files:
            findings.append(Finding(
                id=f"F-TST-{len(findings)+1:03d}",
                category="TEST",
                severity="HIGH",
                confidence="HIGH",
                title="INFERRED: Zero automated test files discovered in repository",
                summary="The repository contains production source code but zero unit or integration test files.",
                impact="Unverified releases lack automated safety nets against regressions and runtime crashes.",
                recommendation="Introduce a standard test runner (e.g., pytest) with baseline sanity test coverage.",
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
