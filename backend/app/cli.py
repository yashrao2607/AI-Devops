"""
DeploySafe Command Line Interface (CLI)
Provides entry point for GitHub Actions workflows, CI/CD pipelines, and local developer runs.

Usage examples:
    python -m backend.app.cli analyze --repo . --ci --output-json report.json --output-md summary.md
    python -m backend.app.cli analyze --repo https://github.com/owner/repo --pr 12 --github-repo owner/repo --ci
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Optional

from backend.app.core.logging import logger
from backend.app.services.rag.loader import RepositoryLoader, RepositoryLoaderError
from backend.app.agents.analysis_flow import DeploySafeAnalysisFlow
from backend.app.services.gate_policy import GatePolicyEngine, GatePolicyConfig
from backend.app.services.github_service import GitHubService, GitHubServiceError


# Ensure UTF-8 output encoding across all platforms
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def parse_args():
    parser = argparse.ArgumentParser(
        prog="deploysafe",
        description="DeploySafe: Multi-Agent AI Pre-Deployment Risk Analysis Platform"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # analyze subcommand
    analyze_parser = subparsers.add_parser("analyze", help="Analyze repository deployment readiness")
    analyze_parser.add_argument(
        "--repo",
        type=str,
        required=True,
        help="Local repository path or remote GitHub URL (e.g. '.' or 'https://github.com/owner/repo')"
    )
    analyze_parser.add_argument("--branch", type=str, default="main", help="Git branch to analyze")
    analyze_parser.add_argument("--commit", type=str, default=None, help="Commit SHA being analyzed")
    analyze_parser.add_argument("--pr", type=int, default=None, help="Pull Request number if triggered by PR")
    analyze_parser.add_argument("--github-repo", type=str, default=None, help="GitHub repository in 'owner/repo' format")
    analyze_parser.add_argument("--output-json", type=str, default=None, help="Path to save machine-readable JSON report")
    analyze_parser.add_argument("--output-md", type=str, default=None, help="Path to save human-readable Markdown summary")
    analyze_parser.add_argument("--ci", action="store_true", help="Enforce CI gate policy exit code (exit 1 on BLOCKED)")
    analyze_parser.add_argument("--publish-github", action="store_true", help="Publish summary comment to GitHub PR if token available")
    analyze_parser.add_argument("--max-risk", type=float, default=None, help="Override maximum allowable risk score")
    analyze_parser.add_argument("--block-critical", action="store_true", default=True, help="Block deployment if any critical findings exist")

    # version subcommand
    subparsers.add_parser("version", help="Print DeploySafe CLI version")

    return parser.parse_args()


def run_analyze(args) -> int:
    """Executes the analysis command and evaluates the deployment gate."""
    print(f"[DeploySafe CLI] Starting Analysis on '{args.repo}'")
    print(f"   Branch: {args.branch} | Commit: {args.commit or 'HEAD'} | PR: #{args.pr or 'N/A'}")

    # Step 1: Load repository snapshot
    try:
        repo_input = args.repo.strip()
        if repo_input.startswith("http://") or repo_input.startswith("https://") or (not os.path.exists(repo_input) and "/" in repo_input):
            print(f"[*] Cloning remote GitHub repository: {repo_input}...")
            snapshot = RepositoryLoader.load_github(repo_input, branch=args.branch)
        else:
            abs_path = os.path.abspath(repo_input)
            print(f"[*] Loading local repository from: {abs_path}...")
            snapshot = RepositoryLoader.load_local(abs_path)
    except RepositoryLoaderError as e:
        print(f"[ERROR] Error loading repository: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"[ERROR] Unexpected system error during repository loading: {e}", file=sys.stderr)
        return 2

    # Step 2: Execute Multi-Agent Analysis Flow
    try:
        print(f"[*] Initiating multi-agent analysis flow...")
        flow = DeploySafeAnalysisFlow()
        report = flow.execute_flow(snapshot, options={
            "pr_number": args.pr,
            "commit_sha": args.commit or snapshot.commit_sha,
            "ci_mode": args.ci
        })
        print(f"[OK] Analysis completed! Run ID: {report.run_id}")
        print(f"   Deterministic Risk Score: {report.risk_score:.1f}/100 ({report.risk_level})")
        print(f"   Validated Findings: {len(report.findings)}")
    except Exception as e:
        print(f"[ERROR] System failure during multi-agent analysis: {e}", file=sys.stderr)
        return 2

    # Step 3: Evaluate Deployment Gate Policy
    finding_counts = getattr(report, "finding_counts_by_severity", {}) or {}
    policy = GatePolicyEngine.get_default_policy()
    if args.max_risk is not None:
        policy.max_risk_score = args.max_risk
    if args.block_critical is not None:
        policy.block_on_critical = args.block_critical

    gate_result = GatePolicyEngine.evaluate(
        risk_score=report.risk_score,
        finding_counts=finding_counts,
        policy=policy
    )

    print(f"\n[GATE] Deployment Gate Decision: [{gate_result.status}]")
    for reason in gate_result.reasons:
        print(f"   - {reason}")

    # Step 4: Generate Reports
    report_dict = report.model_dump(mode="json")
    report_dict["gate_result"] = gate_result.model_dump(mode="json")

    # JSON export
    if args.output_json:
        try:
            out_json_path = os.path.abspath(args.output_json)
            os.makedirs(os.path.dirname(out_json_path), exist_ok=True) if os.path.dirname(out_json_path) else None
            with open(out_json_path, "w", encoding="utf-8") as f:
                json.dump(report_dict, f, indent=2, default=str)
            print(f"[REPORT] Saved machine-readable report to: {out_json_path}")
        except Exception as e:
            print(f"[WARN] Could not write JSON report: {e}", file=sys.stderr)

    # Markdown export
    md_summary = GitHubService.generate_pr_markdown_summary(
        report_data=report_dict,
        gate_status=gate_result.status,
        gate_reasons=gate_result.reasons,
        commit_sha=args.commit or snapshot.commit_sha,
        pr_number=args.pr
    )

    if args.output_md:
        try:
            out_md_path = os.path.abspath(args.output_md)
            os.makedirs(os.path.dirname(out_md_path), exist_ok=True) if os.path.dirname(out_md_path) else None
            with open(out_md_path, "w", encoding="utf-8") as f:
                f.write(md_summary)
            print(f"[REPORT] Saved Markdown summary to: {out_md_path}")
        except Exception as e:
            print(f"[WARN] Could not write Markdown report: {e}", file=sys.stderr)

    # Step 5: Publish to GitHub (if requested)
    if args.publish_github and args.pr and args.github_repo:
        try:
            owner, repo_name = args.github_repo.split("/", 1)
            gh_service = GitHubService()
            if gh_service.is_authenticated:
                print(f"[GITHUB] Publishing PR summary comment to {args.github_repo} PR #{args.pr}...")
                comm_res = gh_service.publish_pr_comment(
                    owner=owner,
                    repo=repo_name,
                    pr_number=args.pr,
                    markdown_body=md_summary,
                    update_existing=True
                )
                print(f"[GITHUB] PR comment {comm_res.action}: {comm_res.html_url or f'ID {comm_res.comment_id}'}")
            else:
                print("[WARN] Skipping GitHub PR publication: GITHUB_TOKEN not configured.")
        except Exception as e:
            print(f"[WARN] Failed to publish to GitHub: {e}", file=sys.stderr)

    # Step 6: Return Exit Code
    if args.ci:
        print(f"\nCI Mode: Exiting with code {gate_result.exit_code} ({gate_result.status})")
        return gate_result.exit_code
    return 0


def main():
    args = parse_args()
    if args.command == "version":
        print("DeploySafe CLI v0.5.0 (Phase 5 GitHub Automation & Safety)")
        sys.exit(0)
    elif args.command == "analyze":
        code = run_analyze(args)
        sys.exit(code)
    else:
        print("DeploySafe CLI. Use 'deploysafe --help' or 'python -m backend.app.cli analyze --help' for usage.")
        sys.exit(0)


if __name__ == "__main__":
    main()
