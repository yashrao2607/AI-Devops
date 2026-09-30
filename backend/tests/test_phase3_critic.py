import os
import pytest
from backend.app.models.analysis_schemas import AnalysisContext, Finding
from backend.app.agents.specialized.critic_agent import CriticAgent

@pytest.fixture
def demo_context():
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "demo-repos", "deploysafe-analysis-demo")
    return AnalysisContext(
        repository_id="test_demo_repo",
        repository_name="deploysafe-analysis-demo",
        root_path=root,
        all_files=["README.md", "requirements.txt", "Dockerfile"]
    )

def test_critic_validates_grounded_finding(demo_context):
    critic = CriticAgent()
    f = Finding(
        id="F-1", category="DEPENDENCY", severity="HIGH", confidence="HIGH",
        title="Unpinned package", summary="Unpinned", impact="CI failure",
        recommendation="Pin version", repository_id="test_demo_repo",
        file_path="requirements.txt", line_start=4, line_end=4,
        evidence="requests", source="deterministic", agent="DependencyAgent", status="NEW"
    )
    updated, decisions = critic.review_findings(demo_context, [f])
    assert decisions[0].decision == "VALIDATED"
    assert updated[0].status == "VALIDATED"

def test_critic_rejects_hallucinated_file(demo_context):
    critic = CriticAgent()
    f = Finding(
        id="F-2", category="CODE", severity="CRITICAL", confidence="HIGH",
        title="Imaginary vulnerability", summary="Invented", impact="Fake",
        recommendation="None", repository_id="test_demo_repo",
        file_path="src/does_not_exist.py", line_start=10, line_end=20,
        evidence="some_fake_code()", source="agentic", agent="CodeAgent", status="NEW"
    )
    updated, decisions = critic.review_findings(demo_context, [f])
    assert decisions[0].decision == "REJECTED"
    assert updated[0].status == "REJECTED"
    assert "Hallucination rejection" in decisions[0].reason

def test_critic_rejects_empty_evidence(demo_context):
    critic = CriticAgent()
    f = Finding(
        id="F-3", category="CONFIGURATION", severity="HIGH", confidence="HIGH",
        title="Missing something", summary="Something missing", impact="Bad",
        recommendation="Fix", repository_id="test_demo_repo",
        file_path="Dockerfile", line_start=1, line_end=1,
        evidence="", source="agentic", agent="ConfigAgent", status="NEW"
    )
    updated, decisions = critic.review_findings(demo_context, [f])
    assert decisions[0].decision == "INSUFFICIENT_EVIDENCE"
    assert updated[0].status == "INSUFFICIENT_EVIDENCE"

def test_critic_identifies_duplicates(demo_context):
    critic = CriticAgent()
    f1 = Finding(
        id="F-4", category="DEPENDENCY", severity="HIGH", confidence="HIGH",
        title="Unpinned requests", summary="Unpinned", impact="CI failure",
        recommendation="Pin", repository_id="test_demo_repo",
        file_path="requirements.txt", line_start=4, line_end=4,
        evidence="requests", source="deterministic", agent="DepAgent1", status="NEW"
    )
    f2 = Finding(
        id="F-5", category="DEPENDENCY", severity="HIGH", confidence="HIGH",
        title="requests unpinned", summary="Unpinned duplicate", impact="CI failure",
        recommendation="Pin", repository_id="test_demo_repo",
        file_path="requirements.txt", line_start=4, line_end=4,
        evidence="requests", source="deterministic", agent="DepAgent2", status="NEW"
    )
    updated, decisions = critic.review_findings(demo_context, [f1, f2])
    assert decisions[0].decision == "VALIDATED"
    assert decisions[1].decision == "DUPLICATE"
    assert decisions[1].duplicate_of_id == "F-4"
    assert updated[1].status == "DUPLICATE"
