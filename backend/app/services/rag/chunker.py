import hashlib
import re
from typing import List, Optional
from pydantic import BaseModel, Field

class RepositoryChunk(BaseModel):
    chunk_id: str
    repository_id: str
    commit_sha: Optional[str] = None
    file_path: str
    language: str
    category: str
    chunk_type: str
    line_start: int
    line_end: int
    file_size: int
    content_hash: str
    content: str

class IntelligentChunker:
    """
    Performs repository-aware semantic chunking on discovered files,
    retaining exact line ranges, content hashes, and deterministic chunk IDs.
    """

    MAX_CHUNK_LINES = 80
    MIN_CHUNK_LINES = 3
    MAX_CHUNK_CHARS = 2500

    @classmethod
    def chunk_file(
        cls,
        repository_id: str,
        relative_path: str,
        content: str,
        language: str,
        category: str,
        commit_sha: Optional[str] = None
    ) -> List[RepositoryChunk]:
        """Routes file content to semantic chunker based on category and language."""
        if not content or not content.strip():
            return []

        lines = content.splitlines()
        file_size = len(content.encode("utf-8"))

        if category == "DOCUMENTATION":
            chunks = cls._chunk_markdown(lines)
        elif category in ("CONFIG", "DOCKER", "CI_CD"):
            chunks = cls._chunk_config(lines, language)
        elif category in ("SOURCE_CODE", "TEST"):
            chunks = cls._chunk_code(lines, language)
        else:
            chunks = cls._chunk_generic(lines)

        # Wrap raw chunks with metadata and deterministic IDs
        repo_chunks: List[RepositoryChunk] = []
        for line_start, line_end, chunk_type, chunk_text in chunks:
            if not chunk_text.strip():
                continue

            content_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
            # Deterministic unique chunk ID
            id_source = f"{repository_id}:{relative_path}:{line_start}:{line_end}:{content_hash[:8]}"
            chunk_id = hashlib.sha256(id_source.encode("utf-8")).hexdigest()[:16]

            repo_chunks.append(
                RepositoryChunk(
                    chunk_id=f"chk_{chunk_id}",
                    repository_id=repository_id,
                    commit_sha=commit_sha,
                    file_path=relative_path,
                    language=language,
                    category=category,
                    chunk_type=chunk_type,
                    line_start=line_start,
                    line_end=line_end,
                    file_size=file_size,
                    content_hash=content_hash,
                    content=chunk_text
                )
            )

        return repo_chunks

    @classmethod
    def _chunk_markdown(cls, lines: List[str]) -> List[tuple[int, int, str, str]]:
        """Chunks Markdown files along headings (#, ##, ###) and sections."""
        chunks = []
        current_lines: List[str] = []
        start_line = 1
        heading_re = re.compile(r"^(#{1,6}\s+.*)$")

        for idx, line in enumerate(lines, start=1):
            if heading_re.match(line) and current_lines:
                chunk_text = "\n".join(current_lines)
                chunks.append((start_line, idx - 1, "markdown_section", chunk_text))
                current_lines = [line]
                start_line = idx
            else:
                current_lines.append(line)
                if len(current_lines) >= cls.MAX_CHUNK_LINES:
                    chunk_text = "\n".join(current_lines)
                    chunks.append((start_line, idx, "markdown_section", chunk_text))
                    current_lines = []
                    start_line = idx + 1

        if current_lines:
            chunks.append((start_line, len(lines), "markdown_section", "\n".join(current_lines)))

        return chunks

    @classmethod
    def _chunk_code(cls, lines: List[str], language: str) -> List[tuple[int, int, str, str]]:
        """Chunks source code honoring class/function/block definitions."""
        chunks = []
        current_lines: List[str] = []
        start_line = 1
        current_type = "code_block"

        # Regex patterns for definitions
        def_pattern = re.compile(r"^(async\s+def\s+|def\s+|class\s+|function\s+|export\s+|public\s+|func\s+|fn\s+)")

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            is_definition = bool(def_pattern.match(stripped))

            if is_definition and len(current_lines) >= cls.MIN_CHUNK_LINES:
                chunk_text = "\n".join(current_lines)
                chunks.append((start_line, idx - 1, current_type, chunk_text))
                current_lines = [line]
                start_line = idx
                current_type = "function" if "def" in stripped or "func" in stripped or "fn" in stripped else "class"
            else:
                current_lines.append(line)
                if len(current_lines) >= cls.MAX_CHUNK_LINES:
                    chunk_text = "\n".join(current_lines)
                    chunks.append((start_line, idx, current_type, chunk_text))
                    current_lines = []
                    start_line = idx + 1
                    current_type = "code_block"

        if current_lines:
            chunks.append((start_line, len(lines), current_type, "\n".join(current_lines)))

        return chunks

    @classmethod
    def _chunk_config(cls, lines: List[str], language: str) -> List[tuple[int, int, str, str]]:
        """Chunks configuration and Docker/YAML files along root keys or instruction blocks."""
        chunks = []
        current_lines: List[str] = []
        start_line = 1
        yaml_root_key = re.compile(r"^[a-zA-Z0-9_\-]+:\s*")
        docker_instruction = re.compile(r"^(FROM|RUN|COPY|ADD|ENV|ENTRYPOINT|CMD|EXPOSE|WORKDIR|USER)\s+", re.IGNORECASE)

        for idx, line in enumerate(lines, start=1):
            is_boundary = False
            if language in ("yaml", "yml") and yaml_root_key.match(line) and not line.startswith(" "):
                is_boundary = True
            elif language == "dockerfile" and docker_instruction.match(line):
                is_boundary = (len(current_lines) >= 8)

            if is_boundary and len(current_lines) >= cls.MIN_CHUNK_LINES:
                chunk_text = "\n".join(current_lines)
                chunks.append((start_line, idx - 1, "config_block", chunk_text))
                current_lines = [line]
                start_line = idx
            else:
                current_lines.append(line)
                if len(current_lines) >= cls.MAX_CHUNK_LINES:
                    chunks.append((start_line, idx, "config_block", "\n".join(current_lines)))
                    current_lines = []
                    start_line = idx + 1

        if current_lines:
            chunks.append((start_line, len(lines), "config_block", "\n".join(current_lines)))

        return chunks

    @classmethod
    def _chunk_generic(cls, lines: List[str]) -> List[tuple[int, int, str, str]]:
        """Generic fallback chunking in windowed blocks."""
        chunks = []
        step = cls.MAX_CHUNK_LINES
        for i in range(0, len(lines), step):
            chunk_slice = lines[i : i + step]
            start_line = i + 1
            end_line = min(i + step, len(lines))
            chunks.append((start_line, end_line, "general", "\n".join(chunk_slice)))
        return chunks
