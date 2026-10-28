# DeploySafe V2 Baseline Record

> **Preservation Rule**: Rule 0 of Phase 7 mandates freezing and documenting the Phase 6 academic submission baseline before initiating any V2 post-release enhancements.

---

## 1. Baseline Metadata
- **Version**: 1.0.0 (Production Release)
- **Git Commit SHA**: `42222be8df342125bbda666245f7c3ddf37a597a`
- **Git Tag**: `v1.0.0-final-submission`
- **Timestamp**: October 2026
- **Status**: Complete & Verified (Phase 6 PASS)

---

## 2. Baseline Evaluation Metrics
Measured directly from the automated benchmark suite (`backend/app/services/evaluator.py`):
- **Benchmark Fixtures**: 5 repositories in `demo-repos/evaluation/` (`clean-repo`, `config-hazard`, `dependency-vuln`, `security-leak`, `docker-root`)
- **Total Test Cases**: 5
- **Issue Detection Rate (Recall)**: **80.0%** (4/5 target cases detected)
- **False Positive Rate**: **0.0%** (0 false positives on clean benchmark repository)
- **Evidence Validity**: **100.0%** (100% of findings grounded in physical repository files & lines)
- **Severity Agreement**: **80.0%**
- **Average Pipeline Runtime**: **4.34 seconds** per evaluation repository
- **Agent Failure Rate**: **0.0%**

---

## 3. Baseline Architectural Profile
- **Orchestration**: `DeploySafeAnalysisFlow` with dynamic planning (`AnalysisPlan`) and Step 5 Partial Failure handling.
- **Agents (6)**: Code Analysis, Configuration Analysis, Dependency Analysis, Test Analysis, Documentation RAG, Security Analysis.
- **Reflection**: Adversarial Critic Agent (`critic_agent.py`) verifying file existence, line bounds, and snippet matching.
- **Risk Engine**: Mathematical 0–100 deterministic scoring with calibrated weights (`CRITICAL`=35, `HIGH`=25, `MEDIUM`=15, `LOW`=7).
- **Gate Policy**: Deterministic gating (`ALLOWED`, `REVIEW_REQUIRED`, `BLOCKED`) enforced in CLI and GitHub Action.
- **Comparison Engine**: Finding fingerprinting (`file_path:line:category:rule_id`) categorizing findings into `Resolved`, `New`, `Persistent`, `Changed`.
- **RAG Subsystem**: ChromaDB vector store with Google `text-embedding-004` (768d) and local fallback.
- **Security**: Pre-ingestion regex secret scrubbing, `<untrusted_repository_content>` prompt isolation.
- **Frontend**: React 18 + Vite SPA, TailwindCSS dark mode, 0 TypeScript errors.

---

## 4. Known Technical Limitations (Baseline)
1. **Static Analysis Scope**: Evaluates static code, configs, Dockerfiles, and manifests; does not execute dynamic microservice cluster fuzzing.
2. **Language Optimization**: Deep AST parsing is optimized for Python, JS/TS, Dockerfile, JSON, and YAML.
3. **Repository Boundaries**: Ingestion bounded at 2,000 files and 200MB.
4. **No Repository-Level Configuration (`deploysafe.yml`)**: Policy thresholds and ignored paths are currently globally configured rather than per-repository.
5. **No Cross-Component Change Impact Mapping**: Git diffs are analyzed per-file without an explicit dependency radius map (e.g., config changes impacting container runtime).

---

## 5. Preservation Guarantee
All Phase 6 submission artifacts (`PHASE6DONE.md`, `RELEASE_NOTES.md`, `docs/viva-guide.md`, `docs/final-demo-script.md`, `docs/contribution-matrix.md`, `docs/final-presentation.md`) remain untouched and preserved. V2 enhancements will strictly extend functionality without degrading baseline performance.
