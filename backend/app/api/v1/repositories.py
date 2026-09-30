import os
import shutil
import tempfile
from typing import Optional, List, Literal
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel, Field
from backend.app.services.rag.loader import RepositoryLoader, RepositorySnapshot, RepositoryLoaderError
from backend.app.services.rag.discovery import FileDiscoveryService, DiscoveredFile
from backend.app.services.rag.indexer import RepositoryIndexer, IndexSummary, _INDEX_STATUS_REGISTRY
from backend.app.services.rag.retriever import RepositoryRetriever, SearchResponse
from backend.app.services.rag.vector_store import ChromaVectorStore
from backend.app.core.logging import logger

router = APIRouter()

# Active snapshots in memory
_ACTIVE_SNAPSHOTS: dict[str, RepositorySnapshot] = {}

class IngestRequest(BaseModel):
    source_type: Literal["local", "github"]
    target: str = Field(description="Local directory path or GitHub URL")
    branch: Optional[str] = "main"
    repository_id: Optional[str] = None

class SearchRequest(BaseModel):
    query: str = Field(description="Natural language question or search phrase")
    top_k: int = Field(default=5, ge=1, le=20)
    category: Optional[str] = None

class RepositoryStatsResponse(BaseModel):
    repository_id: str
    repository_name: str
    vector_count: int
    source_type: str
    file_count: int
    total_size_bytes: int
    status: str

@router.post("/ingest", response_model=RepositorySnapshot)
def ingest_repository(payload: IngestRequest):
    """Ingests a repository from a local filesystem path or public/private GitHub URL."""
    try:
        if payload.source_type == "local":
            snapshot = RepositoryLoader.load_local(path=payload.target, repository_id=payload.repository_id)
        elif payload.source_type == "github":
            snapshot = RepositoryLoader.load_github(url=payload.target, branch=payload.branch, repository_id=payload.repository_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid source type. Use 'local' or 'github'.")

        _ACTIVE_SNAPSHOTS[snapshot.repository_id] = snapshot
        return snapshot
    except RepositoryLoaderError as e:
        logger.error("Ingestion failed: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected ingestion error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@router.post("/ingest-zip", response_model=RepositorySnapshot)
def ingest_zip_archive(file: UploadFile = File(...), repository_id: Optional[str] = Form(None)):
    """Uploads and safely extracts a ZIP archive into a controlled workspace."""
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a .zip archive.")

    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    try:
        shutil.copyfileobj(file.file, temp_zip)
        temp_zip.close()

        snapshot = RepositoryLoader.load_zip(zip_path=temp_zip.name, repository_id=repository_id)
        _ACTIVE_SNAPSHOTS[snapshot.repository_id] = snapshot
        return snapshot
    except RepositoryLoaderError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if os.path.exists(temp_zip.name):
            try:
                os.remove(temp_zip.name)
            except OSError:
                pass

@router.post("/{repository_id}/index", response_model=IndexSummary)
def index_repository_endpoint(repository_id: str):
    """Triggers the full RAG indexing pipeline on an ingested repository."""
    snapshot = _ACTIVE_SNAPSHOTS.get(repository_id)
    if not snapshot:
        # Check if repository exists as local directory fallback
        if os.path.isdir(repository_id):
            snapshot = RepositoryLoader.load_local(repository_id)
            _ACTIVE_SNAPSHOTS[snapshot.repository_id] = snapshot
        else:
            raise HTTPException(status_code=404, detail=f"Repository '{repository_id}' has not been ingested yet.")

    try:
        indexer = RepositoryIndexer()
        summary = indexer.index_repository(snapshot)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

@router.get("/{repository_id}/index-status", response_model=IndexSummary)
def get_index_status(repository_id: str):
    """Returns current indexing state and real progress metrics."""
    summary = RepositoryIndexer.get_status(repository_id)
    if not summary:
        raise HTTPException(status_code=404, detail=f"No indexing job found for '{repository_id}'.")
    return summary

@router.post("/{repository_id}/search", response_model=SearchResponse)
def search_repository_endpoint(repository_id: str, payload: SearchRequest):
    """Performs semantic RAG search across indexed repository chunks, returning evidence."""
    retriever = RepositoryRetriever()
    filters = {"category": payload.category} if payload.category else None
    response = retriever.search_repository_knowledge(
        query=payload.query,
        repository_id=repository_id,
        top_k=payload.top_k,
        filters=filters
    )
    return response

@router.get("/{repository_id}/files", response_model=List[DiscoveredFile])
def get_discovered_files(repository_id: str):
    """Lists discovered files and categorization for an ingested repository."""
    snapshot = _ACTIVE_SNAPSHOTS.get(repository_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail=f"Repository '{repository_id}' not found.")
    return FileDiscoveryService.discover_files(snapshot.root_path)

@router.get("/{repository_id}/stats", response_model=RepositoryStatsResponse)
def get_repository_stats(repository_id: str):
    """Returns storage and vector counts for a repository."""
    vector_store = ChromaVectorStore()
    vec_count = vector_store.count(repository_id)
    snapshot = _ACTIVE_SNAPSHOTS.get(repository_id)
    index_status = RepositoryIndexer.get_status(repository_id)

    return RepositoryStatsResponse(
        repository_id=repository_id,
        repository_name=snapshot.repository_name if snapshot else repository_id,
        vector_count=vec_count,
        source_type=snapshot.source_type if snapshot else "unknown",
        file_count=snapshot.file_count if snapshot else 0,
        total_size_bytes=snapshot.total_size_bytes if snapshot else 0,
        status=index_status.status if index_status else ("INDEXED" if vec_count > 0 else "NOT_INDEXED")
    )
