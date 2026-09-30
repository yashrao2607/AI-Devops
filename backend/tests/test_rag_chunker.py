import pytest
from backend.app.services.rag.chunker import IntelligentChunker

def test_chunk_markdown_along_headings():
    md_content = (
        "# Heading 1\n"
        "Introductory paragraph text.\n\n"
        "## Subheading 2\n"
        "Secondary section details and notes.\n"
    )
    chunks = IntelligentChunker.chunk_file(
        repository_id="test_repo",
        relative_path="README.md",
        content=md_content,
        language="markdown",
        category="DOCUMENTATION"
    )

    assert len(chunks) == 2
    assert chunks[0].line_start == 1
    assert chunks[0].line_end == 3
    assert chunks[1].line_start == 4
    assert chunks[1].line_end == 5
    assert chunks[0].chunk_type == "markdown_section"
    assert chunks[0].chunk_id.startswith("chk_")

def test_chunk_python_functions():
    code = (
        "import os\n\n"
        "def helper_one():\n"
        "    return 1\n\n"
        "class Worker:\n"
        "    def run(self):\n"
        "        pass\n"
    )
    chunks = IntelligentChunker.chunk_file(
        repository_id="test_repo",
        relative_path="src/utils.py",
        content=code,
        language="python",
        category="SOURCE_CODE"
    )

    assert len(chunks) >= 2
    assert all(c.repository_id == "test_repo" for c in chunks)
    assert all(c.file_path == "src/utils.py" for c in chunks)
    assert all(c.content_hash for c in chunks)

def test_chunk_determinism():
    content = "def test():\n    return True\n"
    c1 = IntelligentChunker.chunk_file("repo_a", "app.py", content, "python", "SOURCE_CODE")
    c2 = IntelligentChunker.chunk_file("repo_a", "app.py", content, "python", "SOURCE_CODE")

    assert len(c1) == len(c2)
    assert c1[0].chunk_id == c2[0].chunk_id
    assert c1[0].content_hash == c2[0].content_hash
