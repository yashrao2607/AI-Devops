import pytest
import httpx
from unittest.mock import MagicMock, patch

from backend.app.services.github_service import (
    GitHubService,
    GitHubServiceError,
    GitHubAuthError,
    GitHubRateLimitError,
    GitHubResourceNotFoundError,
    GitHubPRInfo,
    GitHubChangedFile
)


def test_github_service_headers_authenticated():
    svc = GitHubService(token="ghp_test_token_12345")
    assert svc.is_authenticated is True
    headers = svc._get_headers()
    assert headers["Authorization"] == "Bearer ghp_test_token_12345"
    assert "application/vnd.github.v3+json" in headers["Accept"]


def test_github_service_headers_unauthenticated():
    svc = GitHubService(token="")
    assert svc.is_authenticated is False
    headers = svc._get_headers()
    assert "Authorization" not in headers


def test_github_service_error_classification():
    svc = GitHubService(token="dummy")

    # 401 Auth Error
    resp_401 = httpx.Response(401, text="Bad credentials")
    with pytest.raises(GitHubAuthError):
        svc._handle_response_error(resp_401, "test")

    # 403 Rate Limit Error
    resp_403_rate = httpx.Response(403, text="API rate limit exceeded")
    with pytest.raises(GitHubRateLimitError):
        svc._handle_response_error(resp_403_rate, "test")

    # 404 Not Found
    resp_404 = httpx.Response(404, text="Not Found")
    with pytest.raises(GitHubResourceNotFoundError):
        svc._handle_response_error(resp_404, "test")


@patch("httpx.Client.get")
def test_get_pull_request(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "number": 42,
        "title": "feat: add payment processing",
        "state": "open",
        "head": {"ref": "feature/payments", "sha": "head123"},
        "base": {"ref": "main", "sha": "base456"},
        "user": {"login": "dev-user"},
        "html_url": "https://github.com/org/repo/pull/42",
        "changed_files": 3
    }
    mock_get.return_value = mock_resp

    svc = GitHubService(token="token123")
    pr = svc.get_pull_request("org", "repo", 42)

    assert isinstance(pr, GitHubPRInfo)
    assert pr.number == 42
    assert pr.source_branch == "feature/payments"
    assert pr.target_branch == "main"
    assert pr.head_sha == "head123"
    assert pr.changed_files_count == 3


@patch("httpx.Client.get")
def test_get_pull_request_files(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "filename": "Dockerfile",
            "status": "modified",
            "additions": 5,
            "deletions": 2,
            "changes": 7,
            "patch": "@@ -1,2 +1,5 @@\n+EXPOSE 8080"
        },
        {
            "filename": "requirements.txt",
            "status": "modified",
            "additions": 1,
            "deletions": 0,
            "changes": 1,
            "patch": "@@ -1 +1,2 @@\n+requests==2.31.0"
        }
    ]
    mock_get.return_value = mock_resp

    svc = GitHubService(token="token123")
    files = svc.get_pull_request_files("org", "repo", 42)

    assert len(files) == 2
    assert files[0].filename == "Dockerfile"
    assert files[0].additions == 5
    assert files[1].filename == "requirements.txt"


@patch("httpx.Client.patch")
@patch("httpx.Client.get")
def test_publish_pr_comment_idempotent_update(mock_get, mock_patch):
    # Simulate existing comment with marker
    mock_get_resp = MagicMock()
    mock_get_resp.status_code = 200
    mock_get_resp.json.return_value = [
        {"id": 999, "body": f"<!-- DEPLOYSAFE_CI_SUMMARY -->\nOld report"}
    ]
    mock_get.return_value = mock_get_resp

    mock_patch_resp = MagicMock()
    mock_patch_resp.status_code = 200
    mock_patch_resp.json.return_value = {
        "id": 999,
        "html_url": "https://github.com/org/repo/pull/42#issuecomment-999"
    }
    mock_patch.return_value = mock_patch_resp

    svc = GitHubService(token="token123")
    res = svc.publish_pr_comment("org", "repo", 42, "New report summary", update_existing=True)

    assert res.comment_id == 999
    assert res.action == "updated"
    assert mock_patch.called
