import os
from typing import List, Optional
from pydantic import BaseModel
from backend.app.models.analysis_schemas import AnalysisContext
from backend.app.services.tools.safe_executor import SafeCommandExecutor
from backend.app.core.logging import logger

class TestExecutionResult(BaseModel):
    executed: bool
    command: str
    exit_code: int
    tests_passed: int = 0
    tests_failed: int = 0
    raw_output: str
    summary_message: str

class TestTools:
    """
    Test execution tool implementing Step 8 and 12 of Phase 3.
    Executes controlled tests (e.g. pytest) only when explicitly configured,
    strictly distinguishing OBSERVED test outcomes from INFERRED missing tests.
    """
    __test__ = False

    @classmethod
    def run_tests_safe(cls, context: AnalysisContext) -> TestExecutionResult:
        """
        Executes pytest in the repository root if pytest and test files exist.
        Controlled execution with 15s timeout and output bounds.
        """
        test_files = context.files_by_category.get("TEST", [])
        if not test_files:
            return TestExecutionResult(
                executed=False,
                command="",
                exit_code=0,
                raw_output="",
                summary_message="No test files discovered in repository."
            )

        # Execute pytest safely
        cmd = ["pytest", "-v", "--tb=short", "-q"]
        res = SafeCommandExecutor.execute(
            command=cmd,
            cwd=context.root_path,
            timeout=15
        )

        output = res.stdout + "\n" + res.stderr
        passed_count = 0
        failed_count = 0

        # Simple count parsing from pytest summary line
        for line in output.splitlines():
            if "passed" in line:
                for part in line.split(","):
                    if "passed" in part:
                        digits = "".join(filter(str.isdigit, part))
                        if digits:
                            passed_count = int(digits)
                    if "failed" in part:
                        digits = "".join(filter(str.isdigit, part))
                        if digits:
                            failed_count = int(digits)

        summary = (
            f"Pytest executed: {passed_count} passed, {failed_count} failed (Exit: {res.exit_code})"
            if res.exit_code in (0, 1)
            else f"Pytest execution failed or not installed (Exit: {res.exit_code}): {res.stderr[:200]}"
        )

        return TestExecutionResult(
            executed=True,
            command=" ".join(cmd),
            exit_code=res.exit_code,
            tests_passed=passed_count,
            tests_failed=failed_count,
            raw_output=output[:4000],
            summary_message=summary
        )
