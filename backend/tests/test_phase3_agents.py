import os
import pytest
from backend.app.models.analysis_schemas import AnalysisContext
from backend.app.agents.specialized.code_agent import CodeAnalysisAgent
from backend.app.agents.specialized.dependency_agent import DependencyAnalysisAgent
from backend.app.agents.specialized.config_agent import ConfigurationAnalysisAgent
from backend.app.agents.specialized.test_agent import TestAnalysisAgent
from backend.app.agents.specialized.security_agent import SecurityAnalysisAgent

@pytest.fixture
def demo_context():
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "demo-repos", "deploysafe-analysis-demo")
    return AnalysisContext(
        repository_id="test_demo_repo",
        repository_name="deploysafe-analysis-demo",
        root_path=root,
        all_files=[
            "README.md",
            "requirements.txt",
            "Dockerfile",
            "docker-compose.yml",
            "src/app.py",
            "src/payment.py",
            "config/production.py",
            "tests/test_app.py"
        ],
        files_by_category={
            "SOURCE_CODE": ["src/app.py", "src/payment.py"],
            "CONFIG": ["config/production.py"],
            "DOCKER": ["Dockerfile", "docker-compose.yml"],
            "TEST": ["tests/test_app.py"],
            "DOCUMENTATION": ["README.md"]
        }
    )

def test_code_agent_detects_localhost_in_payment(demo_context):
    agent = CodeAnalysisAgent()
    findings = agent.analyze(demo_context)
    assert len(findings) >= 1
    localhost_f = [f for f in findings if "localhost" in f.evidence]
    assert len(localhost_f) >= 1
    assert localhost_f[0].file_path == "src/payment.py"
    assert localhost_f[0].line_start == 9

def test_dependency_agent_detects_unpinned_requests(demo_context):
    agent = DependencyAnalysisAgent()
    findings = agent.analyze(demo_context)
    assert len(findings) >= 1
    unpinned_f = [f for f in findings if "requests" in f.title]
    assert len(unpinned_f) >= 1
    assert unpinned_f[0].category == "DEPENDENCY"
    assert unpinned_f[0].severity == "HIGH"

def test_config_agent_detects_unpinned_docker_image(demo_context):
    agent = ConfigurationAnalysisAgent()
    findings = agent.analyze(demo_context)
    assert len(findings) >= 1
    docker_f = [f for f in findings if "base container image" in f.title.lower() or "dockerfile" in f.file_path.lower()]
    assert len(docker_f) >= 1

def test_test_agent_detects_missing_payment_tests(demo_context):
    agent = TestAnalysisAgent()
    findings = agent.analyze(demo_context)
    assert len(findings) >= 1
    inferred_f = [f for f in findings if "payment" in f.title.lower()]
    assert len(inferred_f) >= 1
    assert "INFERRED" in inferred_f[0].title

def test_security_agent_detects_database_credentials(demo_context):
    agent = SecurityAnalysisAgent()
    findings = agent.analyze(demo_context)
    assert len(findings) >= 1
    sec_f = [f for f in findings if "secret" in f.title.lower() or "database" in f.title.lower()]
    # Verify zero raw password exposure in evidence
    assert "SuperSecretPassword123" not in sec_f[0].evidence
    assert "***REDACTED_SECRET***" in sec_f[0].evidence

from backend.app.agents.specialized.rag_agent import DocumentationRAGAgent
from backend.app.services.rag.indexer import RepositoryIndexer
from backend.app.services.rag.loader import RepositoryLoader

def test_rag_agent_detects_redis_mismatch(demo_context):
    # Ensure demo repo is indexed for RAG
    snapshot = RepositoryLoader.load_local(demo_context.root_path, repository_id=demo_context.repository_id)
    indexer = RepositoryIndexer()
    indexer.index_repository(snapshot)

    agent = DocumentationRAGAgent()
    findings = agent.analyze(demo_context)
    assert len(findings) >= 1
    redis_f = [f for f in findings if "REDIS_URL" in f.title]
    assert len(redis_f) >= 1
    assert redis_f[0].category == "DOCUMENTATION"
    assert redis_f[0].file_path == "docker-compose.yml"
