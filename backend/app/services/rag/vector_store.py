import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Optional, Dict, Any
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.rag.chunker import RepositoryChunk

class VectorStoreError(Exception):
    """Raised when vector store operations fail."""
    pass

class ChromaVectorStore:
    """
    Chroma Vector Store with repository-level isolation, persistent disk storage,
    and metadata filtering.
    """

    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or settings.CHROMA_PATH
        try:
            if self.persist_directory in (":memory:", "memory"):
                self.client = chromadb.EphemeralClient()
                logger.info("Chroma ephemeral in-memory client initialized.")
            else:
                os.makedirs(self.persist_directory, exist_ok=True)
                self.client = chromadb.PersistentClient(path=self.persist_directory)
                logger.info("Chroma persistent client initialized at: %s", self.persist_directory)
        except Exception as e:
            logger.error("Failed to initialize Chroma client: %s", str(e))
            raise VectorStoreError(f"Chroma initialization error: {str(e)}")

    def _get_collection_name(self, repository_id: str) -> str:
        clean_id = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in repository_id)
        return f"repo_{clean_id}"

    def get_or_create_collection(self, repository_id: str):
        col_name = self._get_collection_name(repository_id)
        try:
            return self.client.get_or_create_collection(
                name=col_name,
                metadata={"repository_id": repository_id, "hnsw:space": "cosine"}
            )
        except Exception as e:
            raise VectorStoreError(f"Could not get or create collection '{col_name}': {str(e)}")

    def upsert_chunks(self, repository_id: str, chunks: List[RepositoryChunk], embeddings: List[List[float]]):
        """Batch upserts chunks and vectors into repository collection."""
        if not chunks:
            return

        if len(chunks) != len(embeddings):
            raise VectorStoreError(f"Chunk count ({len(chunks)}) does not match embedding count ({len(embeddings)}).")

        collection = self.get_or_create_collection(repository_id)

        ids = [c.chunk_id for c in chunks]
        documents = [c.content for c in chunks]
        metadatas = [
            {
                "chunk_id": c.chunk_id,
                "repository_id": repository_id,
                "file_path": c.file_path,
                "language": c.language,
                "category": c.category,
                "chunk_type": c.chunk_type,
                "line_start": c.line_start,
                "line_end": c.line_end,
                "content_hash": c.content_hash,
                "commit_sha": c.commit_sha or ""
            }
            for c in chunks
        ]

        try:
            # Batch in increments of 200 for stability
            batch_size = 200
            for i in range(0, len(ids), batch_size):
                end = i + batch_size
                collection.upsert(
                    ids=ids[i:end],
                    embeddings=embeddings[i:end],
                    documents=documents[i:end],
                    metadatas=metadatas[i:end]
                )
            logger.info("Successfully upserted %d chunks into repository collection '%s'", len(chunks), repository_id)
        except Exception as e:
            logger.error("Chroma upsert failed: %s", str(e))
            raise VectorStoreError(f"Failed to upsert chunks: {str(e)}")

    def query(
        self,
        repository_id: str,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Queries repository collection ensuring strict repository isolation."""
        collection = self.get_or_create_collection(repository_id)
        
        # Build where clause enforcing repository isolation
        where_clause = {"repository_id": repository_id}
        if filters:
            for k, v in filters.items():
                where_clause[k] = v

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause
            )
        except Exception as e:
            logger.error("Chroma query error: %s", str(e))
            raise VectorStoreError(f"Vector search failed: {str(e)}")

        formatted = []
        if not results or not results.get("ids") or not results["ids"][0]:
            return formatted

        for idx, chunk_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][idx] if results.get("metadatas") else {}
            doc = results["documents"][0][idx] if results.get("documents") else ""
            distance = results["distances"][0][idx] if results.get("distances") else 1.0
            
            # Convert cosine distance to relevance score (0.0 to 1.0)
            relevance = max(0.0, min(1.0, 1.0 - (distance / 2.0)))

            formatted.append({
                "chunk_id": chunk_id,
                "relevance_score": round(relevance, 4),
                "distance": distance,
                "content": doc,
                "metadata": meta,
                "repository_id": meta.get("repository_id", repository_id),
                "file_path": meta.get("file_path", ""),
                "line_start": meta.get("line_start", 1),
                "line_end": meta.get("line_end", 1),
                "category": meta.get("category", "OTHER"),
                "language": meta.get("language", "unknown"),
                "commit_sha": meta.get("commit_sha", "")
            })

        return formatted

    def count(self, repository_id: str) -> int:
        """Returns total vector count in repository collection."""
        try:
            collection = self.get_or_create_collection(repository_id)
            return collection.count()
        except Exception:
            return 0

    def delete_collection(self, repository_id: str):
        """Deletes collection and vectors for a repository."""
        col_name = self._get_collection_name(repository_id)
        try:
            self.client.delete_collection(name=col_name)
            logger.info("Deleted Chroma collection: %s", col_name)
        except Exception as e:
            logger.debug("Collection '%s' delete notice: %s", col_name, str(e))

    def health_check(self) -> bool:
        """Checks Chroma connectivity."""
        try:
            self.client.heartbeat()
            return True
        except Exception:
            return False
