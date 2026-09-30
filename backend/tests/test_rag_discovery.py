import os
import tempfile
import pytest
from backend.app.services.rag.discovery import FileDiscoveryService

def test_file_discovery_on_demo_repo():
    demo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "demo-repos", "deploysafe-rag-demo")
    files = FileDiscoveryService.discover_files(demo_path)

    assert len(files) >= 5
    categories = {f.category for f in files}
    assert "DOCUMENTATION" in categories  # README.md
    assert "CONFIG" in categories         # requirements.txt / config.py
    assert "DOCKER" in categories         # Dockerfile / docker-compose.yml
    assert "TEST" in categories           # test_app.py

def test_secret_redaction():
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w")
    try:
        temp_file.write(
            "API_KEY = 'AIzaSyA12345678901234567890123456789012'\n"
            "GROQ_KEY = 'gsk_abcdef123456789012345678901234567890123456789012'\n"
            "def connect():\n"
            "    pass\n"
        )
        temp_file.close()

        redacted_text, was_redacted = FileDiscoveryService.read_and_redact_file(temp_file.name)
        assert was_redacted is True
        assert "AIzaSy" not in redacted_text
        assert "gsk_" not in redacted_text
        assert "***REDACTED_SECRET***" in redacted_text
        assert "def connect():" in redacted_text
    finally:
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)
