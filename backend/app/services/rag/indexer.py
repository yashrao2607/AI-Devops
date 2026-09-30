import time
from datetime import datetime
from typing import Dict, Optional, Literal, List
from pydantic import BaseModel, Field
from backend.app.services.rag.loader import RepositorySnapshot, RepositoryLoader
from backend.app.services.rag.discovery import FileDiscoveryService, DiscoveredFile
from backend.app.services.rag.chunker import IntelligentChunker, RepositoryChunk
from backend.app.services.rag.embeddings import EmbeddingFactory, EmbeddingProvider
from backend.app.services.rag.vector_store import ChromaVectorStore
from backend.app.core.logging import logger

IndexingStatus = Literal[
    "QUEUED",
    "INGESTING",
    "DISCOVERING",
    "CHUNKING",
    "EMBEDDING",
    "INDEXING",
    "COMPLETED",
    "FAILED"
]

class IndexSummary(BaseModel):
    repository_id: str
    repository_name: str
    files_discovered: int = 0
    files_indexed: int = 0
    files_skipped: int = 0
    chunks_created: int = 0
    embeddings_created: int = 0
    embedding_failures: int = 0
    total_size_bytes: int = 0
    duration_seconds: float = 0.0
    status: IndexingStatus = "QUEUED"
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None

# Global registry for active repository statuses
_INDEX_STATUS_REGISTRY: Dict[str, IndexSummary] = {}

class RepositoryIndexer:
    """
    End-to-end pipeline orchestrating repository ingestion, discovery,
    secret-aware parsing, intelligent chunking, embedding generation,
    and Chroma vector indexing.
    """

    def __init__(
        self,
        vector_store: Optional[ChromaVectorStore] = None,
        embedding_provider: Optional[EmbeddingProvider] = None
    ):
        self.vector_store = vector_store or ChromaVectorStore()
        self.embedding_provider = embedding_provider or EmbeddingFactory.get_provider()

    @staticmethod
    def get_status(repository_id: str) -> Optional[IndexSummary]:
        return _INDEX_STATUS_REGISTRY.get(repository_id)

    def index_repository(self, snapshot: RepositorySnapshot) -> IndexSummary:
        """Executes the full RAG indexing pipeline synchronously."""
        repo_id = snapshot.repository_id
        start_time = time.time()

        summary = IndexSummary(
            repository_id=repo_id,
            repository_name=snapshot.repository_name,
            total_size_bytes=snapshot.total_size_bytes,
            status="INGESTING"
        )
        _INDEX_STATUS_REGISTRY[repo_id] = summary

        try:
            # 1. File Discovery
            summary.status = "DISCOVERING"
            _INDEX_STATUS_REGISTRY[repo_id] = summary
            discovered = FileDiscoveryService.discover_files(snapshot.root_path)

            summary.files_discovered = len(discovered)
            indexable_files = [f for f in discovered if f.is_indexable]
            summary.files_skipped = len(discovered) - len(indexable_files)

            # 2. Chunking with secret redaction
            summary.status = "CHUNKING"
            _INDEX_STATUS_REGISTRY[repo_id] = summary

            all_chunks: List[RepositoryChunk] = []
            indexed_count = 0

            for f_info in indexable_files:
                try:
                    content, was_redacted = FileDiscoveryService.read_and_redact_file(f_info.absolute_path)
                    f_info.has_redacted_secrets = was_redacted
                    
                    chunks = IntelligentChunker.chunk_file(
                        repository_id=repo_id,
                        relative_path=f_info.relative_path,
                        content=content,
                        language=f_info.language,
                        category=f_info.category,
                        commit_sha=snapshot.commit_sha
                    )
                    if chunks:
                        all_chunks.extend(chunks)
                        indexed_count += 1
                except Exception as fe:
                    logger.warning("Failed to chunk file '%s': %s", f_info.relative_path, str(fe))

            summary.files_indexed = indexed_count
            summary.chunks_created = len(all_chunks)

            if not all_chunks:
                logger.warning("Zero chunks created for repository '%s'", repo_id)
                summary.status = "COMPLETED"
                summary.duration_seconds = round(time.time() - start_time, 2)
                summary.completed_at = datetime.utcnow()
                _INDEX_STATUS_REGISTRY[repo_id] = summary
                return summary

            # 3. Embedding generation
            summary.status = "EMBEDDING"
            _INDEX_STATUS_REGISTRY[repo_id] = summary

            # Context-enriched embedding text incorporates file path and category
            texts = [f"File: {c.file_path}\nCategory: {c.category}\n{c.content}" for c in all_chunks]
            embeddings: List[List[float]] = []

            # Batch embeddings in batches of 50
            batch_size = 50
            fail_count = 0
            for i in range(0, len(texts), batch_size):
                chunk_batch = texts[i : i + batch_size]
                try:
                    batch_vecs = self.embedding_provider.embed_batch(chunk_batch)
                    embeddings.extend(batch_vecs)
                except Exception as ee:
                    logger.error("Embedding batch failed (%d to %d): %s", i, i + len(chunk_batch), str(ee))
                    fail_count += len(chunk_batch)
                    # Fallback to zero vectors or local vectors to prevent total loss
                    fallback = EmbeddingFactory.get_provider(preferred_provider="local")
                    batch_vecs = fallback.embed_batch(chunk_batch)
                    embeddings.extend(batch_vecs)

            summary.embeddings_created = len(embeddings)
            summary.embedding_failures = fail_count

            # 4. Chroma Vector Store indexing
            summary.status = "INDEXING"
            _INDEX_STATUS_REGISTRY[repo_id] = summary

            self.vector_store.upsert_chunks(
                repository_id=repo_id,
                chunks=all_chunks,
                embeddings=embeddings
            )

            # 5. Completion
            summary.status = "COMPLETED"
            summary.duration_seconds = round(time.time() - start_time, 2)
            summary.completed_at = datetime.utcnow()
            _INDEX_STATUS_REGISTRY[repo_id] = summary

            logger.info("Successfully indexed repository '%s': %d files, %d chunks in %.2fs",
                        repo_id, summary.files_indexed, summary.chunks_created, summary.duration_seconds)
            return summary

        except Exception as e:
            logger.error("Indexing failed for repository '%s': %s", repo_id, str(e), exc_info=True)
            summary.status = "FAILED"
            summary.error_message = str(e)
            summary.duration_seconds = round(time.time() - start_time, 2)
            _INDEX_STATUS_REGISTRY[repo_id] = summary
            raise
