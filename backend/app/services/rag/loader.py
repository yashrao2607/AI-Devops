import os
import re
import shutil
import tempfile
import zipfile
import subprocess
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
from backend.app.core.config import settings
from backend.app.core.logging import logger

class RepositorySnapshot(BaseModel):
    source_type: Literal["local", "github", "zip"]
    repository_id: str
    repository_name: str
    branch: Optional[str] = "main"
    commit_sha: Optional[str] = None
    ingestion_timestamp: datetime = Field(default_factory=datetime.utcnow)
    root_path: str
    file_count: int = 0
    total_size_bytes: int = 0
    is_temporary: bool = False

class RepositoryLoaderError(Exception):
    """Raised when repository ingestion fails or security checks fail."""
    pass

class RepositoryLoader:
    """
    Ingests and normalizes software repositories from local directories,
    remote GitHub URLs, and ZIP archives into a unified snapshot.
    """

    MAX_FILE_COUNT = 1500
    MAX_REPO_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
    MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024   # 5 MB

    @staticmethod
    def _sanitize_slug(name: str) -> str:
        clean = re.sub(r"[^a-zA-Z0-9_\-]", "_", name)
        return clean.strip("_") or "repo"

    @classmethod
    def load_local(cls, path: str, repository_id: Optional[str] = None) -> RepositorySnapshot:
        """Loads and validates a local repository directory."""
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            raise RepositoryLoaderError(f"Local path does not exist: {abs_path}")
        if not os.path.isdir(abs_path):
            raise RepositoryLoaderError(f"Local path is not a directory: {abs_path}")
        if not os.access(abs_path, os.R_OK):
            raise RepositoryLoaderError(f"Local directory is not readable: {abs_path}")

        repo_name = os.path.basename(abs_path) or "local_repo"
        repo_id = repository_id or cls._sanitize_slug(repo_name)

        # Inspect git commit and branch if available
        branch = "main"
        commit_sha = None
        git_dir = os.path.join(abs_path, ".git")
        if os.path.exists(git_dir):
            try:
                res_b = subprocess.run(["git", "-C", abs_path, "rev-parse", "--abbrev-ref", "HEAD"],
                                       capture_output=True, text=True, timeout=5)
                if res_b.returncode == 0:
                    branch = res_b.stdout.strip()
                res_c = subprocess.run(["git", "-C", abs_path, "rev-parse", "HEAD"],
                                       capture_output=True, text=True, timeout=5)
                if res_c.returncode == 0:
                    commit_sha = res_c.stdout.strip()
            except Exception as e:
                logger.debug("Could not read git metadata for %s: %s", abs_path, str(e))

        file_count, total_size = cls._calculate_stats(abs_path)
        logger.info("Loaded local repository '%s' (%d files, %d bytes)", repo_name, file_count, total_size)

        return RepositorySnapshot(
            source_type="local",
            repository_id=repo_id,
            repository_name=repo_name,
            branch=branch,
            commit_sha=commit_sha,
            root_path=abs_path,
            file_count=file_count,
            total_size_bytes=total_size,
            is_temporary=False
        )

    @classmethod
    def load_github(cls, url: str, branch: Optional[str] = None, repository_id: Optional[str] = None) -> RepositorySnapshot:
        """Safely clones a public or authenticated GitHub repository."""
        # Validate URL format
        pattern = r"^https://github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+?)(?:\.git)?/?$"
        match = re.match(pattern, url.strip())
        if not match:
            raise RepositoryLoaderError(f"Invalid GitHub repository URL: {url}. Must be in format https://github.com/owner/repo")

        owner, repo_name = match.group(1), match.group(2)
        repo_id = repository_id or f"{cls._sanitize_slug(owner)}_{cls._sanitize_slug(repo_name)}"

        temp_dir = tempfile.mkdtemp(prefix=f"deploysafe_gh_{repo_id}_")
        clone_url = url
        if settings.GITHUB_TOKEN and settings.GITHUB_TOKEN.strip() and not settings.GITHUB_TOKEN.startswith("YOUR_"):
            clone_url = f"https://x-access-token:{settings.GITHUB_TOKEN}@github.com/{owner}/{repo_name}.git"

        cmd = ["git", "clone", "--depth", "1"]
        if branch:
            cmd.extend(["--branch", branch])
        cmd.extend([clone_url, temp_dir])

        try:
            logger.info("Cloning GitHub repository: %s/%s into temp dir %s", owner, repo_name, temp_dir)
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            if res.returncode != 0:
                # Mask token in error message if present
                err_msg = res.stderr.replace(settings.GITHUB_TOKEN or "", "***TOKEN***")
                shutil.rmtree(temp_dir, ignore_errors=True)
                raise RepositoryLoaderError(f"Git clone failed: {err_msg}")
        except subprocess.TimeoutExpired:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RepositoryLoaderError("Git clone timed out after 45 seconds.")
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RepositoryLoaderError(f"Failed to clone GitHub repository: {str(e)}")

        # Fetch commit SHA
        commit_sha = None
        try:
            res_c = subprocess.run(["git", "-C", temp_dir, "rev-parse", "HEAD"],
                                   capture_output=True, text=True, timeout=5)
            if res_c.returncode == 0:
                commit_sha = res_c.stdout.strip()
        except Exception:
            pass

        file_count, total_size = cls._calculate_stats(temp_dir)
        return RepositorySnapshot(
            source_type="github",
            repository_id=repo_id,
            repository_name=f"{owner}/{repo_name}",
            branch=branch or "main",
            commit_sha=commit_sha,
            root_path=temp_dir,
            file_count=file_count,
            total_size_bytes=total_size,
            is_temporary=True
        )

    @classmethod
    def load_zip(cls, zip_path: str, repository_id: Optional[str] = None) -> RepositorySnapshot:
        """Safely extracts a ZIP archive with zip-slip protection and quota limits."""
        abs_zip = os.path.abspath(zip_path)
        if not os.path.exists(abs_zip) or not os.path.isfile(abs_zip):
            raise RepositoryLoaderError(f"ZIP file does not exist: {abs_zip}")

        repo_name = os.path.splitext(os.path.basename(abs_zip))[0]
        repo_id = repository_id or cls._sanitize_slug(repo_name)
        temp_dir = tempfile.mkdtemp(prefix=f"deploysafe_zip_{repo_id}_")

        try:
            with zipfile.ZipFile(abs_zip, "r") as zf:
                # Security checks
                infolist = zf.infolist()
                if len(infolist) > cls.MAX_FILE_COUNT:
                    raise RepositoryLoaderError(f"ZIP archive contains too many files ({len(infolist)} > {cls.MAX_FILE_COUNT}).")

                total_extracted_size = sum(info.file_size for info in infolist)
                if total_extracted_size > cls.MAX_REPO_SIZE_BYTES:
                    raise RepositoryLoaderError(f"Uncompressed ZIP size exceeds limit ({total_extracted_size} > {cls.MAX_REPO_SIZE_BYTES} bytes).")

                # Zip-slip path traversal check
                for info in infolist:
                    target_path = os.path.abspath(os.path.join(temp_dir, info.filename))
                    if not target_path.startswith(os.path.abspath(temp_dir)):
                        raise RepositoryLoaderError(f"Malicious ZIP entry detected (Path Traversal/Zip-Slip): {info.filename}")

                zf.extractall(temp_dir)
        except zipfile.BadZipFile:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RepositoryLoaderError("Invalid or corrupted ZIP archive.")
        except Exception:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise

        file_count, total_size = cls._calculate_stats(temp_dir)
        logger.info("Extracted ZIP archive '%s' (%d files, %d bytes)", repo_name, file_count, total_size)

        return RepositorySnapshot(
            source_type="zip",
            repository_id=repo_id,
            repository_name=repo_name,
            branch=None,
            commit_sha=None,
            root_path=temp_dir,
            file_count=file_count,
            total_size_bytes=total_size,
            is_temporary=True
        )

    @classmethod
    def cleanup_snapshot(cls, snapshot: RepositorySnapshot):
        """Safely cleans up temporary directories if created during ingestion."""
        if snapshot.is_temporary and os.path.exists(snapshot.root_path):
            try:
                shutil.rmtree(snapshot.root_path, ignore_errors=True)
                logger.info("Cleaned up temporary workspace: %s", snapshot.root_path)
            except Exception as e:
                logger.warning("Could not delete temporary directory %s: %s", snapshot.root_path, str(e))

    @classmethod
    def _calculate_stats(cls, root_dir: str) -> tuple[int, int]:
        count = 0
        total_size = 0
        for root, dirs, files in os.walk(root_dir):
            if any(p in root for p in [".git", "node_modules", ".venv", "__pycache__"]):
                continue
            for f in files:
                f_path = os.path.join(root, f)
                try:
                    total_size += os.path.getsize(f_path)
                    count += 1
                except (OSError, FileNotFoundError):
                    pass
        return count, total_size
