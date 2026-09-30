import os
import re
from typing import List, Optional, Literal, Tuple
from pydantic import BaseModel, Field
from backend.app.core.logging import logger

FileCategory = Literal[
    "SOURCE_CODE",
    "TEST",
    "CONFIG",
    "DOCUMENTATION",
    "DOCKER",
    "CI_CD",
    "SCRIPT",
    "OTHER"
]

class DiscoveredFile(BaseModel):
    relative_path: str
    absolute_path: str
    filename: str
    extension: str
    language: str
    category: FileCategory
    size_bytes: int
    is_binary: bool = False
    is_indexable: bool = True
    skip_reason: Optional[str] = None
    has_redacted_secrets: bool = False

class FileDiscoveryService:
    """
    Recursively scans a repository root, applies security and ignore filters,
    detects languages and categories, and performs secret redaction.
    """

    MAX_FILE_SIZE_BYTES = 1 * 1024 * 1024  # 1 MB max for indexed text
    
    IGNORE_DIRECTORIES = {
        ".git", "node_modules", "venv", ".venv", "env", "dist", "build",
        "__pycache__", ".pytest_cache", ".coverage", ".idea", ".vscode",
        "bin", "obj", ".mypy_cache", ".ruff_cache", "chroma_db", "chroma_data"
    }

    IGNORE_EXTENSIONS = {
        # Binary & compiled
        ".exe", ".dll", ".so", ".dylib", ".bin", ".o", ".a", ".pyc", ".class",
        # Images & media
        ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp", ".mp4", ".mp3",
        # Archives
        ".zip", ".tar", ".gz", ".7z", ".rar", ".iso",
        # Databases & caches
        ".db", ".sqlite", ".sqlite3", ".parquet", ".pkl",
        # Minified web assets
        ".min.js", ".min.css", ".map"
    }

    LANGUAGE_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".mjs": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c_header",
        ".hpp": "cpp_header",
        ".php": "php",
        ".rb": "ruby",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".toml": "toml",
        ".xml": "xml",
        ".md": "markdown",
        ".markdown": "markdown",
        ".rst": "rst",
        ".sh": "shell",
        ".bash": "shell",
        ".ps1": "powershell",
        ".sql": "sql",
        "dockerfile": "dockerfile"
    }

    SECRET_REGEXES = [
        re.compile(r"(AIza[0-9A-Za-z-_]{35})"),                      # Google Gemini
        re.compile(r"(gsk_[0-9A-Za-z]{48,})"),                       # Groq Cloud
        re.compile(r"(ghp_[0-9A-Za-z]{36,})"),                       # GitHub Token
        re.compile(r"(AKIA[0-9A-Z]{16})"),                           # AWS Key
        re.compile(r"(-----BEGIN [A-Z ]+ PRIVATE KEY-----)"),        # Private keys
        re.compile(r"(password|secret|token)\s*[:=]\s*['\"][A-Za-z0-9_\-\.\@\#\$\%]{8,}['\"]", re.IGNORECASE)
    ]

    @classmethod
    def discover_files(cls, root_path: str) -> List[DiscoveredFile]:
        """Performs comprehensive recursive discovery on a repository root."""
        abs_root = os.path.abspath(root_path)
        discovered: List[DiscoveredFile] = []

        for current_root, dirs, files in os.walk(abs_root):
            # Prune ignored directory trees
            dirs[:] = [d for d in dirs if d not in cls.IGNORE_DIRECTORIES and not d.startswith(".")]

            for fname in files:
                full_path = os.path.join(current_root, fname)
                rel_path = os.path.relpath(full_path, abs_root).replace("\\", "/")

                file_info = cls._inspect_file(full_path, rel_path, fname)
                discovered.append(file_info)

        logger.info("Discovery complete for '%s': %d total files (%d indexable)",
                    abs_root, len(discovered), sum(1 for f in discovered if f.is_indexable))
        return discovered

    @classmethod
    def _inspect_file(cls, full_path: str, rel_path: str, filename: str) -> DiscoveredFile:
        ext = os.path.splitext(filename)[1].lower()
        size = 0
        try:
            size = os.path.getsize(full_path)
        except (OSError, FileNotFoundError):
            pass

        # Check binary by extension or null byte check
        is_binary = ext in cls.IGNORE_EXTENSIONS
        if not is_binary and size > 0:
            is_binary = cls._is_binary_file(full_path)

        # Detect language
        lower_name = filename.lower()
        if "dockerfile" in lower_name:
            lang = "dockerfile"
        else:
            lang = cls.LANGUAGE_MAP.get(ext, "unknown")

        # Categorize
        category = cls._categorize_file(rel_path, lower_name, ext, lang)

        # Check indexable status
        is_indexable = True
        skip_reason = None

        if is_binary:
            is_indexable = False
            skip_reason = "Binary or compiled file"
        elif size > cls.MAX_FILE_SIZE_BYTES:
            is_indexable = False
            skip_reason = f"File size ({size} bytes) exceeds limit ({cls.MAX_FILE_SIZE_BYTES} bytes)"
        elif ext in cls.IGNORE_EXTENSIONS:
            is_indexable = False
            skip_reason = f"Extension '{ext}' in ignore list"

        return DiscoveredFile(
            relative_path=rel_path,
            absolute_path=full_path,
            filename=filename,
            extension=ext,
            language=lang,
            category=category,
            size_bytes=size,
            is_binary=is_binary,
            is_indexable=is_indexable,
            skip_reason=skip_reason,
            has_redacted_secrets=False
        )

    @classmethod
    def _categorize_file(cls, rel_path: str, lower_name: str, ext: str, lang: str) -> FileCategory:
        path_parts = rel_path.lower().split("/")

        if any(p in ("test", "tests", "__tests__", "spec", "specs") for p in path_parts):
            return "TEST"
        if lower_name.startswith("test_") or lower_name.endswith(("_test.py", ".test.ts", ".test.js", ".spec.ts", ".spec.js")):
            return "TEST"
        if ".github/workflows" in rel_path or "jenkinsfile" in lower_name or ".gitlab-ci" in lower_name:
            return "CI_CD"
        if "docker" in lower_name or lang == "dockerfile":
            return "DOCKER"
        if ext in (".md", ".markdown", ".rst") or "docs" in path_parts or lower_name.startswith("readme"):
            return "DOCUMENTATION"
        if ext in (".sh", ".bash", ".ps1") or "scripts" in path_parts:
            return "SCRIPT"
        if ext in (".yaml", ".yml", ".json", ".toml", ".xml", ".ini", ".cfg", ".env") or lower_name in (
            "requirements.txt", "package.json", "pyproject.toml", "setup.py", "cargo.toml", "pom.xml", "go.mod"
        ):
            return "CONFIG"
        if lang in ("python", "javascript", "typescript", "java", "go", "rust", "c", "cpp", "php", "ruby", "sql"):
            return "SOURCE_CODE"
        return "OTHER"

    @classmethod
    def _is_binary_file(cls, full_path: str) -> bool:
        """Reads initial chunk of file to detect binary bytes."""
        try:
            with open(full_path, "rb") as f:
                chunk = f.read(1024)
                if b"\x00" in chunk:
                    return True
                # Try decoding chunk as UTF-8
                chunk.decode("utf-8")
                return False
        except (UnicodeDecodeError, OSError):
            return True

    @classmethod
    def read_and_redact_file(cls, full_path: str) -> Tuple[str, bool]:
        """
        Reads a text file, applies safe encoding fallback, redacts detected secrets,
        and returns: (redacted_content, was_redacted).
        """
        raw_text = ""
        for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                with open(full_path, "r", encoding=encoding) as f:
                    raw_text = f.read()
                break
            except (UnicodeDecodeError, OSError):
                continue

        was_redacted = False
        redacted_text = raw_text

        for pattern in cls.SECRET_REGEXES:
            if pattern.search(redacted_text):
                was_redacted = True
                redacted_text = pattern.sub("***REDACTED_SECRET***", redacted_text)

        if was_redacted:
            logger.info("Secret redaction applied to file: %s", full_path)

        return redacted_text, was_redacted
