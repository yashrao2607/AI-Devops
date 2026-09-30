import os
import pytest
from backend.app.agents.initial_flow import RepositoryReadinessFlow
from backend.app.models.schemas import ReadinessAssessmentResult

def test_initial_readiness_flow_execution():
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    flow = RepositoryReadinessFlow(repository_path=current_dir)
    result = flow.execute(target_branch="main")

    assert isinstance(result, ReadinessAssessmentResult)
    assert result.overall_risk_level in ("LOW", "MODERATE", "HIGH", "CRITICAL")
    assert 0 <= result.risk_score <= 100
    assert len(result.agent_trace) >= 2
    assert len(result.summary) > 0
