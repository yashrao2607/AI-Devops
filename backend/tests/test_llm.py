import pytest
from pydantic import BaseModel
from backend.app.services.llm.base import LLMAuthenticationError
from backend.app.services.llm.gemini import GeminiProvider
from backend.app.services.llm.groq import GroqProvider
from backend.app.services.llm.factory import LLMFactory, MockDiagnosticProvider

class MockFindingSchema(BaseModel):
    category: str
    severity: str
    risk_score: int

def test_gemini_missing_key_raises_auth_error():
    provider = GeminiProvider(api_key="")
    with pytest.raises(LLMAuthenticationError):
        provider.generate(prompt="Hello")

def test_groq_missing_key_raises_auth_error():
    provider = GroqProvider(api_key="")
    with pytest.raises(LLMAuthenticationError):
        provider.generate(prompt="Hello")

def test_diagnostic_mock_provider():
    mock_provider = MockDiagnosticProvider()
    response = mock_provider.generate(prompt="Test prompt")
    assert "Diagnostic Mode" in response

    structured = mock_provider.generate_structured(prompt="Test prompt", schema=MockFindingSchema)
    assert isinstance(structured, MockFindingSchema)
    assert structured.severity is not None

def test_factory_fallback():
    # Factory without configured keys should default safely to diagnostic mock
    output, provider_name = LLMFactory.generate_with_fallback(prompt="Quick test")
    assert provider_name in ("diagnostic_mock", "gemini", "groq")
    assert len(output) > 0
