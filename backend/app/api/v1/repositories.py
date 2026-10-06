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

def register_snapshot(snapshot: RepositorySnapshot, target_alias: Optional[str] = None):
    """Registers a snapshot under all its identifiers, names, slugs, and URL aliases."""
    if not snapshot:
        return
    _ACTIVE_SNAPSHOTS[snapshot.repository_id] = snapshot
    if snapshot.repository_name:
        _ACTIVE_SNAPSHOTS[snapshot.repository_name] = snapshot

    # Normalized slug variants (e.g. owner_repo vs owner/repo)
    s_id = snapshot.repository_id.strip()
    _ACTIVE_SNAPSHOTS[s_id] = snapshot
    _ACTIVE_SNAPSHOTS[s_id.replace("/", "_")] = snapshot
    _ACTIVE_SNAPSHOTS[s_id.replace("_", "/")] = snapshot

    if snapshot.repository_name:
        s_name = snapshot.repository_name.strip()
        _ACTIVE_SNAPSHOTS[s_name] = snapshot
        _ACTIVE_SNAPSHOTS[s_name.replace("/", "_")] = snapshot
        _ACTIVE_SNAPSHOTS[s_name.replace("_", "/")] = snapshot

    if target_alias:
        t = target_alias.strip()
        _ACTIVE_SNAPSHOTS[t] = snapshot
        t_clean = t.rstrip("/").removesuffix(".git")
        _ACTIVE_SNAPSHOTS[t_clean] = snapshot
        if "github.com/" in t_clean:
            slug = t_clean.split("github.com/")[-1]
            _ACTIVE_SNAPSHOTS[slug] = snapshot
            _ACTIVE_SNAPSHOTS[slug.replace("/", "_")] = snapshot
            _ACTIVE_SNAPSHOTS[slug.replace("_", "/")] = snapshot

def lookup_snapshot(repo_identifier: str) -> Optional[RepositorySnapshot]:
    """Finds a snapshot by ID, slug, URL, or local path across in-memory cache and disk."""
    raw = repo_identifier.strip()
    if not raw:
        return None

    # 1. Direct memory lookup
    if raw in _ACTIVE_SNAPSHOTS:
        return _ACTIVE_SNAPSHOTS[raw]

    clean = raw.rstrip("/").removesuffix(".git")
    if clean in _ACTIVE_SNAPSHOTS:
        return _ACTIVE_SNAPSHOTS[clean]

    slug = clean.split("github.com/")[-1] if "github.com/" in clean else clean
    for candidate in [slug, slug.replace("/", "_"), slug.replace("_", "/")]:
        if candidate in _ACTIVE_SNAPSHOTS:
            return _ACTIVE_SNAPSHOTS[candidate]

    # 2. Check disk in cloned_repos, demo-repos, or direct path
    candidates_to_check = [
        raw,
        os.path.join("cloned_repos", slug.replace("/", "_")),
        os.path.join("cloned_repos", slug),
        os.path.join("demo-repos", raw),
        os.path.join("demo-repos", raw.replace("demo-repos/", "")),
    ]
    for c_path in candidates_to_check:
        if os.path.isdir(c_path):
            try:
                repo_id = slug.replace("/", "_") if "cloned_repos" in c_path else os.path.basename(c_path)
                s = RepositoryLoader.load_local(c_path, repository_id=repo_id)
                if "cloned_repos" in c_path:
                    s.source_type = "github"
                register_snapshot(s, target_alias=raw)
                return s
            except Exception as e:
                logger.debug("Lookup disk load failed for %s: %s", c_path, str(e))

    return None

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

@router.get("", response_model=List[RepositorySnapshot])
def list_repositories():
    """Lists all available ingested, cloned, and demo repositories."""
    seen_ids = set()
    repos: List[RepositorySnapshot] = []

    # 1. From in-memory snapshots
    for snapshot in list(_ACTIVE_SNAPSHOTS.values()):
        if snapshot.repository_id not in seen_ids:
            seen_ids.add(snapshot.repository_id)
            repos.append(snapshot)

    # 2. From cloned_repos directory
    cloned_base = os.path.abspath("cloned_repos")
    if os.path.isdir(cloned_base):
        for entry in os.listdir(cloned_base):
            repo_path = os.path.join(cloned_base, entry)
            git_path = os.path.join(repo_path, ".git")
            if os.path.isdir(repo_path) and os.path.exists(git_path) and entry not in seen_ids:
                try:
                    s = RepositoryLoader.load_local(repo_path, repository_id=entry)
                    if s.file_count > 0:
                        s.source_type = "github"
                        register_snapshot(s)
                        seen_ids.add(entry)
                        repos.append(s)
                except Exception as e:
                    logger.debug("Could not inspect cloned repo %s: %s", entry, str(e))

    # 3. From demo-repos directory
    demo_base = os.path.abspath("demo-repos")
    if os.path.isdir(demo_base):
        for entry in os.listdir(demo_base):
            repo_path = os.path.join(demo_base, entry)
            if os.path.isdir(repo_path) and entry not in seen_ids:
                try:
                    s = RepositoryLoader.load_local(repo_path, repository_id=entry)
                    register_snapshot(s)
                    seen_ids.add(entry)
                    repos.append(s)
                except Exception as e:
                    logger.debug("Could not inspect demo repo %s: %s", entry, str(e))

    return repos

@router.post("/ingest", response_model=RepositorySnapshot)
def ingest_repository(payload: IngestRequest):
    """Ingests a repository from a local filesystem path or public/private GitHub URL."""
    try:
        target = payload.target.strip()
        source_type = payload.source_type

        # Smart source_type auto-detection
        is_url_or_slug = (
            target.startswith("http://")
            or target.startswith("https://")
            or "github.com/" in target
            or ("/" in target and not os.path.isdir(target) and not os.path.exists(target))
        )
        if is_url_or_slug and not os.path.isdir(target):
            source_type = "github"
        elif os.path.isdir(target):
            source_type = "local"

        if source_type == "local":
            snapshot = RepositoryLoader.load_local(path=target, repository_id=payload.repository_id)
        elif source_type == "github":
            snapshot = RepositoryLoader.load_github(url=target, branch=payload.branch, repository_id=payload.repository_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid source type. Use 'local' or 'github'.")

        register_snapshot(snapshot, target_alias=payload.target)
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
        register_snapshot(snapshot)
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
    snapshot = lookup_snapshot(repository_id)
    if not snapshot:
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
    snapshot = lookup_snapshot(repository_id)
    retriever = RepositoryRetriever()
    filters = {"category": payload.category} if payload.category else None
    actual_id = snapshot.repository_id if snapshot else repository_id
    response = retriever.search_repository_knowledge(
        query=payload.query,
        repository_id=actual_id,
        top_k=payload.top_k,
        filters=filters
    )
    return response

@router.get("/{repository_id}/files", response_model=List[DiscoveredFile])
def get_discovered_files(repository_id: str):
    """Lists discovered files and categorization for an ingested repository."""
    snapshot = lookup_snapshot(repository_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail=f"Repository '{repository_id}' not found.")
    return FileDiscoveryService.discover_files(snapshot.root_path)

@router.get("/{repository_id}/stats", response_model=RepositoryStatsResponse)
def get_repository_stats(repository_id: str):
    """Returns storage and vector counts for a repository."""
    snapshot = lookup_snapshot(repository_id)
    actual_id = snapshot.repository_id if snapshot else repository_id
    vector_store = ChromaVectorStore()
    vec_count = vector_store.count(actual_id)
    index_status = RepositoryIndexer.get_status(actual_id)

    return RepositoryStatsResponse(
        repository_id=actual_id,
        repository_name=snapshot.repository_name if snapshot else repository_id,
        vector_count=vec_count,
        source_type=snapshot.source_type if snapshot else "unknown",
        file_count=snapshot.file_count if snapshot else 0,
        total_size_bytes=snapshot.total_size_bytes if snapshot else 0,
        status=index_status.status if index_status else ("INDEXED" if vec_count > 0 else "NOT_INDEXED")
    )

@router.get("/{repository_id}/summary")
def get_repository_summary(repository_id: str):
    """
    Returns latest analysis risk score, risk level, and health overview
    for a specific ingested repository.
    """
    from backend.app.agents.analysis_flow import DeploySafeAnalysisFlow

    snapshot = lookup_snapshot(repository_id)
    actual_id = snapshot.repository_id if snapshot else repository_id

    # Check for matching reports
    reports = DeploySafeAnalysisFlow.list_reports()
    matching_reports = [r for r in reports if r.repository_id in (repository_id, actual_id) or repository_id in r.repository_name]
    latest_report = None
    if matching_reports:
        matching_reports.sort(key=lambda r: r.analyzed_at, reverse=True)
        latest_report = matching_reports[0]

    return {
        "repository_id": actual_id,
        "repository_name": snapshot.repository_name if snapshot else (latest_report.repository_name if latest_report else repository_id),
        "has_analysis": latest_report is not None,
        "latest_run_id": latest_report.run_id if latest_report else None,
        "risk_score": latest_report.risk_score if latest_report else None,
        "risk_level": latest_report.risk_level if latest_report else "UNKNOWN",
        "findings_count": len(latest_report.findings) if latest_report else 0,
        "validated_count": len(latest_report.validated_findings) if latest_report else 0,
        "analyzed_at": latest_report.analyzed_at.isoformat() if latest_report else None,
        "summary": latest_report.summary if latest_report else "No deployment risk analyses have been recorded for this repository."
    }

