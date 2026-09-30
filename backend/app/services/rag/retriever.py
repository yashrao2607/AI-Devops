from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from backend.app.services.rag.embeddings import EmbeddingFactory, EmbeddingProvider
from backend.app.services.rag.vector_store import ChromaVectorStore
from backend.app.core.logging import logger

class SearchResult(BaseModel):
    chunk_id: str
    relevance_score: float = Field(description="Cosine relevance score between 0.0 and 1.0")
    file_path: str
    line_start: int
    line_end: int
    category: str
    language: str
    content: str
    commit_sha: Optional[str] = None

class SearchResponse(BaseModel):
    query: str
    repository_id: str
    status: Literal["FOUND", "NOT_FOUND", "LOW_RELEVANCE"]
    results_count: int
    results: List[SearchResult]
    message: Optional[str] = None

class RepositoryRetriever:
    """
    Retrieval service executing semantic vector search against indexed repository chunks
    and formatting traceable evidence with exact file & line references.
    """

    MIN_RELEVANCE_THRESHOLD = 0.52
    HIGH_RELEVANCE_THRESHOLD = 0.58

    def __init__(
        self,
        vector_store: Optional[ChromaVectorStore] = None,
        embedding_provider: Optional[EmbeddingProvider] = None
    ):
        self.vector_store = vector_store or ChromaVectorStore()
        self.embedding_provider = embedding_provider or EmbeddingFactory.get_provider()

    def search_repository_knowledge(
        self,
        query: str,
        repository_id: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> SearchResponse:
        """
        Performs semantic retrieval across repository vectors.
        Enforces repository isolation and anti-hallucination relevance threshold.
        """
        clean_query = query.strip()
        if not clean_query:
            return SearchResponse(
                query=query,
                repository_id=repository_id,
                status="NOT_FOUND",
                results_count=0,
                results=[],
                message="Search query was empty."
            )

        # Check collection vector count
        total_chunks = self.vector_store.count(repository_id)
        if total_chunks == 0:
            return SearchResponse(
                query=clean_query,
                repository_id=repository_id,
                status="NOT_FOUND",
                results_count=0,
                results=[],
                message=f"Repository '{repository_id}' is not indexed or contains 0 vectors."
            )

        # Generate query embedding
        query_vec = self.embedding_provider.embed_text(clean_query)
        raw_results = self.vector_store.query(
            repository_id=repository_id,
            query_embedding=query_vec,
            top_k=top_k,
            filters=filters
        )

        if not raw_results:
            return SearchResponse(
                query=clean_query,
                repository_id=repository_id,
                status="NOT_FOUND",
                results_count=0,
                results=[],
                message="No sufficiently relevant repository evidence was found."
            )

        results: List[SearchResult] = []
        for item in raw_results:
            results.append(
                SearchResult(
                    chunk_id=item["chunk_id"],
                    relevance_score=item["relevance_score"],
                    file_path=item["file_path"],
                    line_start=item["line_start"],
                    line_end=item["line_end"],
                    category=item["category"],
                    language=item["language"],
                    content=item["content"],
                    commit_sha=item["commit_sha"] or None
                )
            )

        # Evaluate anti-hallucination relevance
        top_score = results[0].relevance_score if results else 0.0
        if not results or top_score < self.MIN_RELEVANCE_THRESHOLD:
            status = "NOT_FOUND"
            results = []
            message = "No sufficiently relevant repository evidence was found."
        elif top_score < self.HIGH_RELEVANCE_THRESHOLD:
            status = "LOW_RELEVANCE"
            message = "Low confidence match: retrieved repository snippets have weak semantic similarity."
        else:
            status = "FOUND"
            message = f"Found {len(results)} relevant evidence snippets."

        logger.info("Search query '%s' on repo '%s': %d results (status: %s, top: %.3f)",
                    clean_query, repository_id, len(results), status, top_score)

        return SearchResponse(
            query=clean_query,
            repository_id=repository_id,
            status=status,
            results_count=len(results),
            results=results,
            message=message
        )
