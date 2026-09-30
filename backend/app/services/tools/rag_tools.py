from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from backend.app.services.rag.retriever import RepositoryRetriever, SearchResponse, SearchResult
from backend.app.models.analysis_schemas import Evidence
from backend.app.core.logging import logger

class RAGQueryItem(BaseModel):
    file_path: str
    line_start: int
    line_end: int
    relevance_score: float
    category: str
    content: str

class RAGQueryResult(BaseModel):
    query: str
    status: str
    results_count: int
    evidence_available: bool
    items: List[RAGQueryItem]
    message: Optional[str] = None

class RAGTools:
    """
    RAG Tool providing specialized agents with semantic retrieval
    over the repository's indexed Chroma vector store.
    """

    @staticmethod
    def search_repository_context(
        repository_id: str,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None
    ) -> RAGQueryResult:
        """
        Executes semantic vector search against repository chunks via Phase 2 Retriever.
        Returns verifiable evidence items.
        """
        retriever = RepositoryRetriever()
        filters = {"category": category} if category else None

        try:
            resp: SearchResponse = retriever.search_repository_knowledge(
                query=query,
                repository_id=repository_id,
                top_k=top_k,
                filters=filters
            )

            items = [
                RAGQueryItem(
                    file_path=hit.file_path,
                    line_start=hit.line_start,
                    line_end=hit.line_end,
                    relevance_score=hit.relevance_score,
                    category=hit.category,
                    content=hit.content
                )
                for hit in resp.results
            ]

            return RAGQueryResult(
                query=resp.query,
                status=resp.status,
                results_count=resp.results_count,
                evidence_available=(resp.status == "FOUND" and len(items) > 0),
                items=items,
                message=resp.message
            )

        except Exception as e:
            logger.error("RAG tool query error on repository '%s': %s", repository_id, str(e))
            return RAGQueryResult(
                query=query,
                status="NOT_FOUND",
                results_count=0,
                evidence_available=False,
                items=[],
                message=f"RAG retrieval failed: {str(e)}"
            )
