import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.models.analysis_schemas import AnalysisContext, Evidence
from backend.app.services.tools.safe_executor import SafeCommandExecutor
from backend.app.core.logging import logger

class FileContentResult(BaseModel):
    file_path: str
    line_start: int
    line_end: int
    total_lines: int
    content: str
    exists: bool

class GitDiffResult(BaseModel):
    has_diff: bool
    changed_files: List[str]
    diff_text: str

class DependencyManifestResult(BaseModel):
    manifest_type: str
    file_path: str
    dependencies: List[str]
    raw_content: str

class RepositoryTools:
    """
    Typed deterministic tools providing factual repository ground-truth
    to specialized analysis agents.
    """

    @staticmethod
    def get_repository_files(context: AnalysisContext) -> List[str]:
        """Lists all indexable files in the repository context."""
        return context.all_files

    @staticmethod
    def get_file_content(
        context: AnalysisContext,
        file_path: str,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None
    ) -> FileContentResult:
        """
        Reads actual lines from a repository file safely.
        Validates path traversal to ensure reads stay strictly inside repository root.
        """
        norm_path = os.path.normpath(file_path).lstrip(r"\/")
        full_path = os.path.normpath(os.path.join(context.root_path, norm_path))

        # Path traversal guard
        if not full_path.startswith(os.path.normpath(context.root_path)):
            logger.warning("Attempted path traversal in get_file_content: %s", file_path)
            return FileContentResult(
                file_path=file_path,
                line_start=1,
                line_end=1,
                total_lines=0,
                content="ACCESS_DENIED: Path resolves outside repository boundary.",
                exists=False
            )

        if not os.path.isfile(full_path):
            return FileContentResult(
                file_path=file_path,
                line_start=1,
                line_end=1,
                total_lines=0,
                content="FILE_NOT_FOUND",
                exists=False
            )

        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            total = len(lines)
            start = max(1, line_start or 1)
            end = min(total, line_end or total)

            if total == 0:
                return FileContentResult(
                    file_path=file_path,
                    line_start=1,
                    line_end=1,
                    total_lines=0,
                    content="",
                    exists=True
                )

            selected = lines[start - 1 : end]
            return FileContentResult(
                file_path=file_path,
                line_start=start,
                line_end=end,
                total_lines=total,
                content="".join(selected),
                exists=True
            )

        except Exception as e:
            logger.error("Error reading file '%s': %s", full_path, str(e))
            return FileContentResult(
                file_path=file_path,
                line_start=1,
                line_end=1,
                total_lines=0,
                content=f"ERROR_READING_FILE: {str(e)}",
                exists=False
            )

    @staticmethod
    def get_git_diff(context: AnalysisContext) -> GitDiffResult:
        """
        Extracts git diff for the repository if it is a git repo.
        Falls back to detecting all files if working on an initial snapshot.
        """
        git_dir = os.path.join(context.root_path, ".git")
        if not os.path.isdir(git_dir):
            return GitDiffResult(
                has_diff=False,
                changed_files=context.changed_files or context.all_files[:10],
                diff_text="[Initial repository snapshot - full repository context active]"
            )

        # Attempt git diff against HEAD or staging
        res = SafeCommandExecutor.execute(
            command=["git", "diff", "HEAD~1..HEAD"],
            cwd=context.root_path,
            timeout=10
        )

        if res.exit_code == 0 and res.stdout.strip():
            # Parse changed files from diff output
            changed = []
            for line in res.stdout.splitlines():
                if line.startswith("+++ b/"):
                    changed.append(line[6:])
            return GitDiffResult(
                has_diff=True,
                changed_files=changed or context.changed_files,
                diff_text=res.stdout
            )

        # Check status / unstaged changes if HEAD diff was empty
        res_stat = SafeCommandExecutor.execute(
            command=["git", "status", "--short"],
            cwd=context.root_path,
            timeout=5
        )

        changed = []
        if res_stat.exit_code == 0:
            for line in res_stat.stdout.splitlines():
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    changed.append(parts[1])

        return GitDiffResult(
            has_diff=bool(changed),
            changed_files=changed or context.changed_files or context.all_files[:10],
            diff_text=res_stat.stdout if changed else "[Working tree clean - analyzing snapshot]"
        )

    @staticmethod
    def get_dependency_manifests(context: AnalysisContext) -> List[DependencyManifestResult]:
        """Discovers and parses dependency manifests in the repository."""
        manifest_names = {
            "requirements.txt": "python_pip",
            "pyproject.toml": "python_poetry",
            "package.json": "nodejs_npm",
            "go.mod": "golang_mod",
            "pom.xml": "java_maven",
            "Cargo.toml": "rust_cargo"
        }

        results = []
        for file_path in context.all_files:
            fname = os.path.basename(file_path)
            if fname in manifest_names:
                m_type = manifest_names[fname]
                content_res = RepositoryTools.get_file_content(context, file_path)
                if content_res.exists:
                    # Simple dependency line extraction
                    deps = []
                    for line in content_res.content.splitlines():
                        line_clean = line.strip()
                        if line_clean and not line_clean.startswith("#"):
                            deps.append(line_clean)
                    results.append(DependencyManifestResult(
                        manifest_type=m_type,
                        file_path=file_path,
                        dependencies=deps,
                        raw_content=content_res.content
                    ))
        return results

    @staticmethod
    def get_test_files(context: AnalysisContext) -> List[str]:
        """Discovers test suites and test files in repository."""
        return [
            f for f in context.all_files
            if f in context.files_by_category.get("TEST", [])
            or any(t in f.lower() for t in ["test", "spec", "_test.py", ".spec.ts", ".test.js"])
        ]
