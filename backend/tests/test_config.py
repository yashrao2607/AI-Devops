import os
import pytest
from backend.app.core.config import Settings

def test_settings_load_defaults():
    settings = Settings()
    assert settings.PROJECT_NAME == "DeploySafe"
    assert settings.VERSION == "0.1.0"
    assert settings.API_PORT == 8000
    assert settings.DATABASE_URL.startswith("sqlite")

def test_active_provider_logic_missing_keys():
    # With empty keys, it should fall back safely to diagnostic_mock
    settings = Settings(GEMINI_API_KEY="", GROQ_API_KEY="")
    assert settings.has_gemini is False
    assert settings.has_groq is False
    assert settings.get_active_provider() == "diagnostic_mock"

def test_placeholder_key_ignored():
    # If keys are placeholders like 'YOUR_GEMINI_API_KEY_HERE', they should not be treated as real
    settings = Settings(GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE")
    assert settings.has_gemini is False
