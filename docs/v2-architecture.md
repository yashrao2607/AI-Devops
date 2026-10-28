# DeploySafe V2 — Architecture & Enhancement Specification

## 1. Overview & Architectural Goals

DeploySafe V2 (Phase 7) is an empirical enhancement layer built atop the frozen, verified DeploySafe v1.0.0 academic release (`commit 42222be`, tag `v1.0.0-final-submission`). 

The primary architectural goals of V2 are:
1. **Repository-Specific Governance**: Allow teams to declaratively configure risk tolerance, custom thresholds, and path exclusions via a version-controlled `deploysafe.yml` configuration file.
2. **Deterministic Change Impact Analysis**: Compute physical architectural blast radius and targeted verification checks directly from git diff changes, preventing unexpected ripple effects.
3. **Repository Risk History & Trends**: Enable engineering leads to view historical risk velocity, regression trends, and recurring finding patterns over time across multiple deployment evaluations.
4. **Human-in-the-Loop Remediation Assistance**: Provide previewable unified diff patches for validated code findings, strictly requiring human review and approval before any change can be merged.

---

## 2. Component Diagram

```
+--------------------------------------------------------------------------+
|                            V2 Web Dashboard                              |
|   - Runs View: Run Fingerprint Compare & Change Impact Tab               |
|   - Findings View: Unified Diff Patch Preview Modal + Disclaimer         |
|   - Analytics View: Historical Risk Velocity & Recurring Findings       |
+------------------------------------+-------------------------------------+
                                     | HTTP / JSON REST
+------------------------------------v-------------------------------------+
|                      DeploySafe FastAPI Backend                          |
|                                                                          |
|   [/api/v1/runs/{id}/impact]          [/api/v1/findings/{id}/patch]     |
|   [/api/v1/repositories/{id}/analytics] [/api/v1/runs/{id}/compare]     |
+------------------+------------------------------------+------------------+
                   |                                    |
+------------------v------------------+ +---------------v------------------+
|      RepoConfigService              | |       ChangeImpactService        |
| - Secure `deploysafe.yml` loading   | | - Deterministic file-to-layer    |
| - Traversal & command rejection     | |   blast radius calculation       |
| - Fail-safe production defaults     | | - Required verification checks   |
+------------------+------------------+ +---------------+------------------+
                   |                                    |
+------------------v------------------+ +---------------v------------------+
|       GatePolicyEngine              | |     HistoryAnalyticsService      |
| - Custom thresholds & severity caps | | - Historical risk score series   |
| - Integration with RepoConfig       | | - Gate pass/fail rate tracking   |
| - Strict validation guarantees      | | - Recurring finding detection    |
+-------------------------------------+ +----------------------------------+
                   |
+------------------v------------------+
|           PatchService              |
| - Deterministic unified diff engine |
| - Read-only proposal generation     |
| - Strict human approval guarantee   |
+-------------------------------------+
```

---

## 3. Core Subsystems

### 3.1 Repository Configuration Engine (`RepoConfigService`)
- **Module**: `backend/app/services/repo_config.py`
- **Purpose**: Discovers and parses repository-level rules while preventing untrusted code execution or arbitrary file reading.
- **Security Boundaries**:
  - Rejects path traversal (`..` or absolute paths in target root).
  - Enforces safe bounded ranges (e.g., `fail_threshold` clamped between 0 and 100).
  - Validates all input through strict Pydantic schemas.
  - Safe fallbacks: If absent or unparseable, standard v1.0.0 defaults are used automatically.

### 3.2 Change Impact Engine (`ChangeImpactService`)
- **Module**: `backend/app/services/change_impact.py`
- **Purpose**: Maps physical changed files to structural blast radius:
  - `CRITICAL`: Changes touching DB migrations, authentication/authorization modules, kernel/container configs, or production secrets.
  - `HIGH`: Changes touching core API routes, payment/billing workflows, or shared backend services.
  - `MEDIUM`: Changes touching frontend templates, CSS/assets, or localized utility functions.
  - `LOW`: Documentation, markdown notes, comments, or test mocks.
- **Actionable Checks**: Emits mandatory verification checks (e.g., "Run database migration dry-run and verify rollback script" when migration files are modified).

### 3.3 Historical Analytics Engine (`HistoryAnalyticsService`)
- **Module**: `backend/app/services/history_analytics.py`
- **Purpose**: Computes multi-run aggregate telemetry from physically stored runs:
  - Risk score progression timeline (earliest to latest).
  - Gate pass/fail ratio and block rate.
  - Recurring findings detection: fingerprints matching findings across 2 or more separate runs.
  - Average resolution velocity (time elapsed between detection and remediation).

### 3.4 Remediation Patch Service (`PatchService`)
- **Module**: `backend/app/services/patch_service.py`
- **Purpose**: Generates standard unified diff (`diff -u`) representations of proposed fixes.
- **Safety Protocol**:
  - Strictly non-destructive and read-only.
  - Explicit human approval required; no automated committing or PR opening.
  - Displays visible disclaimer in UI: *"Proposed patch must be reviewed and tested by a human engineer before applying."*

---

## 4. Preservation of Baseline Integrity

All V2 additions are purely additive:
1. No existing v1.0.0 database schemas were destructively altered.
2. The core 5-agent LangGraph orchestration pipeline remains intact and backwards-compatible.
3. Every V2 endpoint degrades gracefully to default behavior if V2 metadata is unavailable for older runs.
