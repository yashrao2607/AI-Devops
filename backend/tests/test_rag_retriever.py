import pytest
from backend.app.services.rag.chunker import RepositoryChunk
from backend.app.services.rag.embeddings import LocalEmbeddingProvider
from backend.app.services.rag.vector_store import ChromaVectorStore
from backend.app.services.rag.retriever import RepositoryRetriever

@pytest.fixture
def populated_retriever():
    store = ChromaVectorStore(persist_directory=":memory:")
    embedder = LocalEmbeddingProvider(dim=384)

    chunks = [
        RepositoryChunk(
            chunk_id="chk_docker",
            repository_id="demo_svc",
            file_path="Dockerfile",
            language="dockerfile",
            category="DOCKER",
            chunk_type="config_block",
            line_start=1,
            line_end=8,
            file_size=150,
            content_hash="h_doc",
            content="# Docker container runtime configuration\nFROM python:3.11\nEXPOSE 8080\nCMD ['uvicorn', 'app:app']"
        ),
        RepositoryChunk(
            chunk_id="chk_test",
            repository_id="demo_svc",
            file_path="README.md",
            language="markdown",
            category="DOCUMENTATION",
            chunk_type="markdown_section",
            line_start=15,
            line_end=22,
            file_size=200,
            content_hash="h_tst",
            content="## Testing Instructions\nRun the test suite with pytest tests/ -v"
        ),
    ]

    vecs = [embedder.embed_text(f"File: {c.file_path}\nCategory: {c.category}\n{c.content}") for c in chunks]
    store.upsert_chunks("demo_svc", chunks, vecs)

    retriever = RepositoryRetriever(vector_store=store, embedding_provider=embedder)
    return retriever

def test_retrieval_docker_query(populated_retriever):
    retriever = populated_retriever
    response = retriever.search_repository_knowledge("Where is the Docker container configured?", "demo_svc")

    assert response.status == "FOUND"
    assert response.results_count >= 1
    top_hit = response.results[0]
    assert "docker" in top_hit.file_path.lower()
    assert top_hit.line_start == 1
    assert "FROM python" in top_hit.content

def test_retrieval_empty_or_unknown_repo(populated_retriever):
    retriever = populated_retriever
    response = retriever.search_repository_knowledge("Any query", "unknown_repo_id")
    assert response.status == "NOT_FOUND"
    assert response.results_count == 0
