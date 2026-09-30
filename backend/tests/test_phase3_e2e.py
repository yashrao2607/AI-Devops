import os
import pytest
from backend.app.services.rag.loader import RepositoryLoader
from backend.app.services.rag.indexer import RepositoryIndexer
from backend.app.services.rag.vector_store import ChromaVectorStore
from backend.app.services.rag.embeddings import LocalEmbeddingProvider
from backend.app.agents.analysis_flow import DeploySafeAnalysisFlow

def test_full_multi_agent_flow_on_demo_repo():
    demo_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "demo-repos",
        "deploysafe-analysis-demo"
    )

    # 1. Ingest repository snapshot
    snapshot = RepositoryLoader.load_local(demo_path, repository_id="e2e_phase3_repo")
    assert snapshot.file_count >= 6

    # 2. Index in memory vector store for RAG
    store = ChromaVectorStore(persist_directory=":memory:")
    embedder = LocalEmbeddingProvider(dim=384)
    indexer = RepositoryIndexer(vector_store=store, embedding_provider=embedder)
    summary = indexer.index_repository(snapshot)
    assert summary.status == "COMPLETED"

    # 3. Execute Multi-Agent Flow
    flow = DeploySafeAnalysisFlow(run_id="test_run_e2e_001")
    report = flow.execute_flow(snapshot)

    # 4. Verify Flow Execution & Report
    assert report.status == "COMPLETED"
    assert report.run_id == "test_run_e2e_001"
    assert len(report.agents_executed) >= 6
    assert "critic" in report.agents_executed
    assert "report" in report.agents_executed

    # 5. Verify Findings generated across multiple agents
    assert len(report.findings) >= 4
    categories = {f.category for f in report.findings}
    assert "CODE" in categories or "DEPENDENCY" in categories
    assert "CONFIGURATION" in categories or "CONTAINERIZATION" in categories or "SECURITY" in categories

    # 6. Verify Critic validation
    assert len(report.validated_findings) >= 2
    for f in report.validated_findings:
        assert f.status == "VALIDATED"
        assert f.critic_notes is not None

    # 7. Verify Security & Secret Redaction
    for f in report.findings:
        assert "SuperSecretPassword123" not in f.evidence
        assert "SuperSecretPassword123" not in f.summary

    # 8. Verify Severity Counts in report
    counts = report.finding_counts_by_severity
    assert (counts["CRITICAL"] + counts["HIGH"] + counts["MEDIUM"] + counts["LOW"]) == len(report.validated_findings) + len(report.needs_review_findings)
    assert len(report.recommendations) >= 1
