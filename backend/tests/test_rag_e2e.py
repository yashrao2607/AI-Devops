import os
import pytest
from backend.app.services.rag.loader import RepositoryLoader
from backend.app.services.rag.indexer import RepositoryIndexer
from backend.app.services.rag.retriever import RepositoryRetriever
from backend.app.services.rag.vector_store import ChromaVectorStore
from backend.app.services.rag.embeddings import LocalEmbeddingProvider

def test_full_rag_pipeline_on_demo_repo():
    demo_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "demo-repos",
        "deploysafe-rag-demo"
    )

    # Isolated in-memory vector store for test
    store = ChromaVectorStore(persist_directory=":memory:")
    embedder = LocalEmbeddingProvider(dim=384)

    # 1. Ingestion
    snapshot = RepositoryLoader.load_local(demo_path, repository_id="e2e_demo_repo")
    assert snapshot.file_count >= 5

    # 2. Indexing
    indexer = RepositoryIndexer(vector_store=store, embedding_provider=embedder)
    summary = indexer.index_repository(snapshot)

    assert summary.status == "COMPLETED"
    assert summary.files_discovered >= 5
    assert summary.files_indexed >= 4
    assert summary.chunks_created >= 5
    assert summary.embeddings_created == summary.chunks_created
    assert summary.duration_seconds > 0

    # 3. Retrieval
    retriever = RepositoryRetriever(vector_store=store, embedding_provider=embedder)

    # Query A: Docker
    res_docker = retriever.search_repository_knowledge("Where is the Docker deployment configured?", "e2e_demo_repo")
    assert res_docker.status == "FOUND"
    docker_files = [hit.file_path for hit in res_docker.results]
    assert any("docker" in f.lower() for f in docker_files)

    # Query B: Testing
    res_test = retriever.search_repository_knowledge("How are tests executed in this project?", "e2e_demo_repo")
    assert res_test.status == "FOUND"
    test_files = [hit.file_path for hit in res_test.results]
    assert any("readme" in f.lower() or "test" in f.lower() for f in test_files)

    # Query C: Environment variables
    res_env = retriever.search_repository_knowledge("Where are database environment variables documented?", "e2e_demo_repo")
    assert res_env.status == "FOUND"
    env_files = [hit.file_path for hit in res_env.results]
    assert any("readme" in f.lower() or "config" in f.lower() for f in env_files)
