import pytest
from backend.app.services.rag.chunker import RepositoryChunk
from backend.app.services.rag.embeddings import LocalEmbeddingProvider
from backend.app.services.rag.vector_store import ChromaVectorStore

@pytest.fixture
def temp_vector_store():
    store = ChromaVectorStore(persist_directory=":memory:")
    return store

def test_chroma_upsert_and_query(temp_vector_store):
    store = temp_vector_store
    embedder = LocalEmbeddingProvider(dim=384)

    chunk = RepositoryChunk(
        chunk_id="chk_101",
        repository_id="repo_alpha",
        file_path="src/config.py",
        language="python",
        category="CONFIG",
        chunk_type="code_block",
        line_start=1,
        line_end=10,
        file_size=200,
        content_hash="abc12345",
        content="DATABASE_URL = 'postgresql://localhost:5432/appdb'"
    )

    vec = embedder.embed_text(chunk.content)
    store.upsert_chunks("repo_alpha", [chunk], [vec])

    assert store.count("repo_alpha") == 1

    query_vec = embedder.embed_text("Where is the database configured?")
    results = store.query("repo_alpha", query_vec, top_k=2)

    assert len(results) == 1
    assert results[0]["chunk_id"] == "chk_101"
    assert results[0]["file_path"] == "src/config.py"
    assert "DATABASE_URL" in results[0]["content"]

def test_repository_isolation(temp_vector_store):
    store = temp_vector_store
    embedder = LocalEmbeddingProvider(dim=384)

    # Repository A
    chunk_a = RepositoryChunk(
        chunk_id="chk_a",
        repository_id="repo_a",
        file_path="secret_a.txt",
        language="text",
        category="OTHER",
        chunk_type="block",
        line_start=1,
        line_end=1,
        file_size=50,
        content_hash="hash_a",
        content="Alpha repository confidential deployment notes."
    )
    store.upsert_chunks("repo_a", [chunk_a], [embedder.embed_text(chunk_a.content)])

    # Repository B
    chunk_b = RepositoryChunk(
        chunk_id="chk_b",
        repository_id="repo_b",
        file_path="secret_b.txt",
        language="text",
        category="OTHER",
        chunk_type="block",
        line_start=1,
        line_end=1,
        file_size=50,
        content_hash="hash_b",
        content="Beta repository confidential deployment notes."
    )
    store.upsert_chunks("repo_b", [chunk_b], [embedder.embed_text(chunk_b.content)])

    # Query Repository A - MUST NOT return Repository B
    query_vec = embedder.embed_text("confidential deployment notes")
    results_a = store.query("repo_a", query_vec, top_k=5)
    
    assert len(results_a) == 1
    assert results_a[0]["repository_id"] == "repo_a"
    assert results_a[0]["chunk_id"] == "chk_a"
    assert all(r["repository_id"] == "repo_a" for r in results_a)
