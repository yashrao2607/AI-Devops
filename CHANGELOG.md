# Changelog

All notable changes to the DeploySafe platform will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - Phase 7 / V2 Post-Release Enhancement - 2026-10-28

### Added
- **Repository-Level Configuration (`deploysafe.yml`)**: Support for declarative policy configuration, custom risk thresholds, and excluded file patterns (`RepoConfigService`).
- **Deterministic Change Impact Analysis**: Physical structural blast radius (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) calculation from git diff changes with required verification checks (`ChangeImpactService`).
- **Endpoint `GET /api/v1/runs/{id}/impact`**: Returns structured blast radius and affected component breakdown.
- **Historical Risk Analytics**: Multi-run timeline analytics, gate pass/fail block rates, and recurring issue detection (`HistoryAnalyticsService`).
- **Endpoint `GET /api/v1/repositories/{id}/analytics`**: Returns historical score trends and resolution velocity.
- **Unified Diff Patch Preview**: Non-destructive standard unified diff generation with human-in-the-loop review disclaimer (`PatchService`).
- **Endpoint `GET /api/v1/findings/{id}/patch`**: Generates proposed patch diffs for code findings.
- **Frontend V2 Enhancements**:
  - Added *Change Impact (V2)* sub-tab in Runs details modal.
  - Added *Preview Proposed Patch* button and modal in Findings page with syntax highlighting and safety disclaimer banner.
- **Comprehensive V2 Test Suite**: Added 6 new integration tests in `backend/tests/test_phase7_v2.py`, bringing total automated tests to 98 passing.

### Changed
- Integrated `policy_from_repo_config` into `GatePolicyEngine` to allow repository configs to override global defaults safely.
- Enhanced `lookup_snapshot` to resolve repository slug aliases consistently across all endpoints.

### Security
- Added path normalization and traversal blocking (`..` rejection) when discovering and loading `deploysafe.yml`.
- Guaranteed human-in-the-loop approval: AI agents are strictly prohibited from auto-committing or merging patches without developer review.

---

## [1.0.0] - Phase 6 Final Academic Release - 2026-10-28
- **Commit**: `42222be8df342125bbda666245f7c3ddf37a597a`
- **Tag**: `v1.0.0-final-submission`
- Complete multi-agent pre-deployment risk platform with 5 specialized agents, LangGraph orchestration, adversarial reflection critic, ChromaDB vector store RAG, deterministic risk scoring (0–100), automated gate policies (`ALLOWED`, `REVIEW_REQUIRED`, `BLOCKED`), run fingerprint diff comparison, React/Vite dashboard, CLI tool, and GitHub Action.
