import os
import pytest
from backend.app.services.tools.safe_executor import SafeCommandExecutor
from backend.app.services.tools.repo_tools import RepositoryTools
from backend.app.services.tools.security_tools import SecurityTools
from backend.app.models.analysis_schemas import AnalysisContext

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

def test_safe_executor_disallows_unauthorized_binaries(tmp_path):
    res = SafeCommandExecutor.execute(["powershell", "-c", "dir"], cwd=str(tmp_path))
    assert res.exit_code == -1
    assert "not in the DeploySafe execution allowlist" in res.stderr

def test_safe_executor_allows_git(tmp_path):
    res = SafeCommandExecutor.execute(["git", "--version"], cwd=str(tmp_path))
    # git may or may not be in test container, but it must not be rejected by allowlist
    assert "not in the DeploySafe execution allowlist" not in res.stderr

def test_repo_tools_read_valid_file(demo_context):
    res = RepositoryTools.get_file_content(demo_context, "requirements.txt")
    assert res.exists is True
    assert "fastapi" in res.content
    assert res.total_lines >= 4

def test_repo_tools_path_traversal_defense(demo_context):
    res = RepositoryTools.get_file_content(demo_context, "../../secret.txt")
    assert res.exists is False
    assert "ACCESS_DENIED" in res.content

def test_repo_tools_manifest_discovery(demo_context):
    manifests = RepositoryTools.get_dependency_manifests(demo_context)
    assert len(manifests) >= 1
    assert any("requirements.txt" in m.file_path for m in manifests)

def test_security_tools_detects_hardcoded_database_secret(demo_context):
    scan_res = SecurityTools.run_security_scan(demo_context)
    assert scan_res.total_findings >= 1
    # Check for redacted secret
    db_findings = [f for f in scan_res.items if "SuperSecretPassword123" not in f.evidence_snippet]
    assert len(db_findings) >= 1
    assert any("***REDACTED_SECRET***" in f.evidence_snippet for f in scan_res.items)
