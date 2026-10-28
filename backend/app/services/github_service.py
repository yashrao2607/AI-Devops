"""
DeploySafe GitHub Integration Service
Provides a clean, secure abstraction over the GitHub REST API (v3)
for pull request inspection, commit diffs, check runs, and idempotent PR commenting.
"""

import os
import re
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import httpx

from backend.app.core.config import settings
from backend.app.core.logging import logger


class GitHubServiceError(Exception):
    """Base exception for GitHub service operations."""
    pass


class GitHubAuthError(GitHubServiceError):
    """Raised when authentication fails (401/403)."""
    pass


class GitHubRateLimitError(GitHubServiceError):
    """Raised when GitHub API rate limit is exceeded (429/403 rate limit)."""
    pass


class GitHubResourceNotFoundError(GitHubServiceError):
    """Raised when repository, commit, or pull request is not found (404)."""
    pass


class GitHubRepoInfo(BaseModel):
    owner: str
    name: str
    full_name: str
    default_branch: str
    is_private: bool
    html_url: str
    description: Optional[str] = None


class GitHubCommitInfo(BaseModel):
    sha: str
    message: str
    author: Optional[str] = None
    authored_date: Optional[str] = None
    html_url: str


class GitHubChangedFile(BaseModel):
    filename: str
    status: str  # added, modified, removed, renamed
    additions: int = 0
    deletions: int = 0
    changes: int = 0
    patch: Optional[str] = None


class GitHubPRInfo(BaseModel):
    number: int
    title: str
    state: str
    source_branch: str
    target_branch: str
    head_sha: str
    base_sha: str
    author: Optional[str] = None
    html_url: str
    changed_files_count: int = 0


class GitHubCommentResult(BaseModel):
    comment_id: int
    action: str  # "created" or "updated"
    html_url: str


class GitHubCheckRunResult(BaseModel):
    check_run_id: int
    name: str
    status: str
    conclusion: Optional[str] = None
    html_url: str


class GitHubService:
    """
    Client for interacting with the GitHub REST API.
    Designed to fail gracefully and maintain least-privilege principles.
    """

    COMMENT_MARKER = "<!-- DEPLOYSAFE_CI_SUMMARY -->"

    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        self.token = token or settings.GITHUB_TOKEN or os.getenv("GITHUB_TOKEN", "")
        self.base_url = base_url.rstrip("/")

    @property
    def is_authenticated(self) -> bool:
        return bool(self.token and self.token.strip() and not self.token.startswith("YOUR_"))

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DeploySafe-CI-Agent/0.1.0"
        }
        if self.is_authenticated:
            # GitHub recommends Bearer token format
            headers["Authorization"] = f"Bearer {self.token.strip()}"
        return headers

    def _handle_response_error(self, response: httpx.Response, context: str):
        if response.status_code == 401:
            raise GitHubAuthError(f"GitHub authentication failed during {context}. Check GITHUB_TOKEN.")
        elif response.status_code == 403:
            if "rate limit" in response.text.lower():
                raise GitHubRateLimitError(f"GitHub API rate limit exceeded during {context}.")
            raise GitHubAuthError(f"GitHub permission denied during {context}: {response.text}")
        elif response.status_code == 404:
            raise GitHubResourceNotFoundError(f"Requested GitHub resource not found during {context}.")
        elif response.status_code >= 400:
            raise GitHubServiceError(f"GitHub API error during {context} (HTTP {response.status_code}): {response.text[:200]}")

    def get_repository(self, owner: str, repo: str) -> GitHubRepoInfo:
        """Fetches repository metadata from GitHub."""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, headers=self._get_headers())
            self._handle_response_error(resp, f"get_repository({owner}/{repo})")
            data = resp.json()
            return GitHubRepoInfo(
                owner=data.get("owner", {}).get("login", owner),
                name=data.get("name", repo),
                full_name=data.get("full_name", f"{owner}/{repo}"),
                default_branch=data.get("default_branch", "main"),
                is_private=data.get("private", False),
                html_url=data.get("html_url", f"https://github.com/{owner}/{repo}"),
                description=data.get("description")
            )

    def get_commit(self, owner: str, repo: str, sha: str) -> GitHubCommitInfo:
        """Fetches specific commit information."""
        url = f"{self.base_url}/repos/{owner}/{repo}/commits/{sha}"
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, headers=self._get_headers())
            self._handle_response_error(resp, f"get_commit({owner}/{repo}, {sha})")
            data = resp.json()
            commit_data = data.get("commit", {})
            author_data = data.get("author") or {}
            return GitHubCommitInfo(
                sha=data.get("sha", sha),
                message=commit_data.get("message", ""),
                author=author_data.get("login") or commit_data.get("author", {}).get("name"),
                authored_date=commit_data.get("author", {}).get("date"),
                html_url=data.get("html_url", "")
            )

    def get_pull_request(self, owner: str, repo: str, pr_number: int) -> GitHubPRInfo:
        """Fetches Pull Request metadata."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, headers=self._get_headers())
            self._handle_response_error(resp, f"get_pull_request({owner}/{repo}, #{pr_number})")
            data = resp.json()
            return GitHubPRInfo(
                number=data.get("number", pr_number),
                title=data.get("title", ""),
                state=data.get("state", "open"),
                source_branch=data.get("head", {}).get("ref", "unknown"),
                target_branch=data.get("base", {}).get("ref", "main"),
                head_sha=data.get("head", {}).get("sha", ""),
                base_sha=data.get("base", {}).get("sha", ""),
                author=data.get("user", {}).get("login"),
                html_url=data.get("html_url", ""),
                changed_files_count=data.get("changed_files", 0)
            )

    def get_pull_request_files(self, owner: str, repo: str, pr_number: int) -> List[GitHubChangedFile]:
        """Fetches the list of files modified in a pull request."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(url, headers=self._get_headers(), params={"per_page": 100})
            self._handle_response_error(resp, f"get_pull_request_files({owner}/{repo}, #{pr_number})")
            items = resp.json()
            return [
                GitHubChangedFile(
                    filename=item.get("filename", ""),
                    status=item.get("status", "modified"),
                    additions=item.get("additions", 0),
                    deletions=item.get("deletions", 0),
                    changes=item.get("changes", 0),
                    patch=item.get("patch")
                )
                for item in items
            ]

    def get_pull_request_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """Fetches the raw git unified diff for a pull request."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = self._get_headers()
        headers["Accept"] = "application/vnd.github.v3.diff"
        with httpx.Client(timeout=25.0) as client:
            resp = client.get(url, headers=headers)
            self._handle_response_error(resp, f"get_pull_request_diff({owner}/{repo}, #{pr_number})")
            return resp.text

    def publish_pr_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        markdown_body: str,
        update_existing: bool = True
    ) -> GitHubCommentResult:
        """
        Publishes a markdown summary comment to a pull request.
        If update_existing=True, searches for an existing DeploySafe comment
        and updates it to prevent PR comment spam.
        """
        if not self.is_authenticated:
            raise GitHubAuthError("Cannot publish GitHub PR comment without a valid GITHUB_TOKEN.")

        # Ensure the hidden marker is present for idempotent updates
        body = markdown_body
        if self.COMMENT_MARKER not in body:
            body = f"{self.COMMENT_MARKER}\n{markdown_body}"

        with httpx.Client(timeout=15.0) as client:
            existing_comment_id = None
            if update_existing:
                comments_url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
                c_resp = client.get(comments_url, headers=self._get_headers(), params={"per_page": 50})
                if c_resp.status_code == 200:
                    comments = c_resp.json()
                    for c in comments:
                        if self.COMMENT_MARKER in c.get("body", ""):
                            existing_comment_id = c.get("id")
                            break

            if existing_comment_id:
                # Update existing comment
                patch_url = f"{self.base_url}/repos/{owner}/{repo}/issues/comments/{existing_comment_id}"
                patch_resp = client.patch(patch_url, headers=self._get_headers(), json={"body": body})
                self._handle_response_error(patch_resp, f"update_pr_comment({existing_comment_id})")
                data = patch_resp.json()
                logger.info("Updated existing DeploySafe comment #%d on PR #%d", existing_comment_id, pr_number)
                return GitHubCommentResult(
                    comment_id=data.get("id", existing_comment_id),
                    action="updated",
                    html_url=data.get("html_url", "")
                )
            else:
                # Create new comment
                post_url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
                post_resp = client.post(post_url, headers=self._get_headers(), json={"body": body})
                self._handle_response_error(post_resp, f"create_pr_comment({owner}/{repo}, #{pr_number})")
                data = post_resp.json()
                logger.info("Posted new DeploySafe comment #%d on PR #%d", data.get("id", 0), pr_number)
                return GitHubCommentResult(
                    comment_id=data.get("id", 0),
                    action="created",
                    html_url=data.get("html_url", "")
                )

    def publish_check_run(
        self,
        owner: str,
        repo: str,
        head_sha: str,
        name: str = "DeploySafe Readiness Gate",
        conclusion: str = "success",  # success, failure, neutral, action_required
        title: str = "Deployment Risk Assessment",
        summary: str = "",
        text: Optional[str] = None
    ) -> GitHubCheckRunResult:
        """
        Creates or updates a GitHub Check Run (Check Suites API) for the commit.
        Requires 'checks: write' permission.
        """
        if not self.is_authenticated:
            raise GitHubAuthError("Cannot publish GitHub Check Run without a valid GITHUB_TOKEN.")

        url = f"{self.base_url}/repos/{owner}/{repo}/check-runs"
        payload = {
            "name": name,
            "head_sha": head_sha,
            "status": "completed",
            "conclusion": conclusion,
            "output": {
                "title": title,
                "summary": summary,
                "text": text or summary
            }
        }
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, headers=self._get_headers(), json=payload)
            self._handle_response_error(resp, f"publish_check_run({owner}/{repo}, {head_sha})")
            data = resp.json()
            return GitHubCheckRunResult(
                check_run_id=data.get("id", 0),
                name=data.get("name", name),
                status=data.get("status", "completed"),
                conclusion=data.get("conclusion", conclusion),
                html_url=data.get("html_url", "")
            )

    @staticmethod
    def generate_pr_markdown_summary(
        report_data: Dict[str, Any],
        gate_status: str,
        gate_reasons: List[str],
        commit_sha: Optional[str] = None,
        pr_number: Optional[int] = None
    ) -> str:
        """
        Generates a beautiful, concise, professional GitHub PR Markdown summary table.
        """
        risk_score = report_data.get("risk_score", 0.0)
        risk_level = report_data.get("risk_level", "LOW")
        run_id = report_data.get("run_id", "unknown")
        findings = report_data.get("findings", [])
        counts = report_data.get("finding_counts_by_severity") or report_data.get("finding_counts", {})
        crit = counts.get("CRITICAL", 0)
        high = counts.get("HIGH", 0)
        med = counts.get("MEDIUM", 0)
        low = counts.get("LOW", 0)

        # Gate badge emoji
        gate_emoji = "✅" if gate_status == "ALLOWED" else ("⚠️" if gate_status == "REVIEW_REQUIRED" else "🛑")
        risk_badge = f"**{risk_level} ({risk_score:.1f}/100)**"

        lines = [
            f"## {gate_emoji} DeploySafe Analysis — Gate Status: `{gate_status}`",
            "",
            f"DeploySafe evaluated this pull request using deterministic multi-agent risk scoring and static analysis.",
            "",
            "| Metric | Value |",
            "| :--- | :--- |",
            f"| **Overall Risk Score** | {risk_badge} |",
            f"| **Deployment Gate** | `{gate_status}` |",
            f"| **Total Findings** | `{len(findings)}` ({crit} Critical, {high} High, {med} Medium, {low} Low) |",
            f"| **Run ID** | `{run_id}` |",
            f"| **Target Commit** | `{commit_sha[:8] if commit_sha else 'HEAD'}` |",
            ""
        ]

        if gate_reasons:
            lines.append("### 🚦 Gate Decision Details")
            for r in gate_reasons:
                lines.append(f"- {r}")
            lines.append("")

        if findings:
            lines.append("### 🔍 Top Deployment Findings")
            lines.append("| Severity | Category | File | Finding Summary |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for f in findings[:5]:
                sev = f.get("severity", "LOW")
                cat = f.get("category", "CODE")
                fpath = f.get("file_path", "-")
                line_no = f.get("line_start")
                loc = f"`{fpath}:{line_no}`" if line_no else f"`{fpath}`"
                title = f.get("title", "")
                lines.append(f"| **{sev}** | `{cat}` | {loc} | {title} |")
            lines.append("")

        lines.append("---")
        lines.append(f"*Automated report generated by [DeploySafe](https://github.com/yashrao2607/NAVEEN-SIR_PROJECT) · Run ID: `{run_id}`*")
        return "\n".join(lines)
