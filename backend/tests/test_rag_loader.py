import os
import zipfile
import tempfile
import pytest
from backend.app.services.rag.loader import RepositoryLoader, RepositoryLoaderError

def test_load_local_repository():
    demo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "demo-repos", "deploysafe-rag-demo")
    snapshot = RepositoryLoader.load_local(demo_path)

    assert snapshot.source_type == "local"
    assert snapshot.repository_name == "deploysafe-rag-demo"
    assert snapshot.file_count >= 5
    assert snapshot.total_size_bytes > 0
    assert os.path.exists(snapshot.root_path)

def test_load_local_invalid_path():
    with pytest.raises(RepositoryLoaderError):
        RepositoryLoader.load_local("/non/existent/path/for/deploysafe/test")

def test_load_zip_archive():
    demo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "demo-repos", "deploysafe-rag-demo")
    
    # Create temporary zip archive
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    try:
        with zipfile.ZipFile(temp_zip.name, "w") as zf:
            for root, _, files in os.walk(demo_path):
                for f in files:
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, demo_path)
                    zf.write(full, rel)
        temp_zip.close()

        snapshot = RepositoryLoader.load_zip(temp_zip.name, repository_id="zip_test_repo")
        assert snapshot.source_type == "zip"
        assert snapshot.repository_id == "zip_test_repo"
        assert snapshot.file_count >= 5
        assert snapshot.is_temporary is True

        # Clean up snapshot
        RepositoryLoader.cleanup_snapshot(snapshot)
        assert not os.path.exists(snapshot.root_path)
    finally:
        if os.path.exists(temp_zip.name):
            os.remove(temp_zip.name)

def test_zip_slip_prevention():
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    try:
        with zipfile.ZipFile(temp_zip.name, "w") as zf:
            zf.writestr("../../evil.txt", "Malicious content")
        temp_zip.close()

        with pytest.raises(RepositoryLoaderError, match="Path Traversal"):
            RepositoryLoader.load_zip(temp_zip.name)
    finally:
        if os.path.exists(temp_zip.name):
            os.remove(temp_zip.name)
