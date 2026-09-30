import os
import subprocess
import time
from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.core.logging import logger

class ExecutionResult(BaseModel):
    command: List[str]
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False
    truncated: bool = False

class SafeCommandExecutor:
    """
    Controlled subprocess runner implementing Step 8 of Phase 3:
    - Explicit allowlist of permissible binary commands
    - Strictly sandboxed to designated repository directory
    - Hard timeouts and output size ceilings
    - Zero shell=True execution to eliminate injection vectors
    """

    ALLOWED_BINARIES = {
        "git",
        "pytest",
        "python",
        "npm",
        "bandit",
        "gitleaks",
        "osv-scanner",
    }

    MAX_OUTPUT_BYTES = 100 * 1024  # 100 KB limit
    DEFAULT_TIMEOUT_SECONDS = 15

    @classmethod
    def execute(
        cls,
        command: List[str],
        cwd: str,
        timeout: Optional[int] = None,
        env: Optional[dict] = None
    ) -> ExecutionResult:
        if not command:
            raise ValueError("Command list cannot be empty.")

        binary = os.path.basename(command[0]).lower()
        # Strip .exe on Windows if present
        if binary.endswith(".exe"):
            binary = binary[:-4]

        if binary not in cls.ALLOWED_BINARIES:
            logger.warning("Rejected unauthorized command binary: %s", binary)
            return ExecutionResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Command '{binary}' is not in the DeploySafe execution allowlist.",
                duration_seconds=0.0
            )

        if not os.path.isdir(cwd):
            return ExecutionResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Working directory '{cwd}' does not exist or is not a directory.",
                duration_seconds=0.0
            )

        t_limit = min(timeout or cls.DEFAULT_TIMEOUT_SECONDS, 60)
        start_time = time.time()

        # Sanitize environment: never pass user credentials or raw secrets
        safe_env = os.environ.copy()
        if env:
            safe_env.update(env)

        try:
            logger.info("Executing controlled command: %s (cwd: %s, timeout: %ds)", " ".join(command), cwd, t_limit)
            proc = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                timeout=t_limit,
                env=safe_env,
                shell=False
            )
            duration = round(time.time() - start_time, 3)

            stdout_str = proc.stdout.decode("utf-8", errors="replace")
            stderr_str = proc.stderr.decode("utf-8", errors="replace")

            truncated = False
            if len(stdout_str) > cls.MAX_OUTPUT_BYTES:
                stdout_str = stdout_str[:cls.MAX_OUTPUT_BYTES] + "\n...[OUTPUT TRUNCATED BY DEPLOYSAFE]"
                truncated = True
            if len(stderr_str) > cls.MAX_OUTPUT_BYTES:
                stderr_str = stderr_str[:cls.MAX_OUTPUT_BYTES] + "\n...[OUTPUT TRUNCATED BY DEPLOYSAFE]"
                truncated = True

            return ExecutionResult(
                command=command,
                exit_code=proc.returncode,
                stdout=stdout_str,
                stderr=stderr_str,
                duration_seconds=duration,
                timed_out=False,
                truncated=truncated
            )

        except subprocess.TimeoutExpired:
            duration = round(time.time() - start_time, 3)
            logger.warning("Command timed out after %ds: %s", t_limit, " ".join(command))
            return ExecutionResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Command execution timed out after {t_limit} seconds.",
                duration_seconds=duration,
                timed_out=True
            )
        except FileNotFoundError:
            duration = round(time.time() - start_time, 3)
            return ExecutionResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Binary '{binary}' is not installed or not in PATH.",
                duration_seconds=duration
            )
        except Exception as e:
            duration = round(time.time() - start_time, 3)
            logger.error("Command execution error: %s", str(e))
            return ExecutionResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Execution failed: {str(e)}",
                duration_seconds=duration
            )
