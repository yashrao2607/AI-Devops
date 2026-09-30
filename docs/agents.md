# DeploySafe Multi-Agent Architecture (Phase 3)

## 1. Overview & Philosophy
DeploySafe transforms deterministic static analysis and RAG knowledge retrieval into an autonomous, collaborative multi-agent intelligence layer. Rather than relying on a single monolithic LLM prompt—which suffers from hallucinations, context dilution, and lack of accountability—DeploySafe orchestrates specialized autonomous agents with typed tool contracts, anti-hallucination guardrails, and an independent Critic validation gatekeeper.

```
                           Repository / Git Diff
                                    ↓
                         Analysis Context Builder
                                    ↓
                            Orchestrator Agent
                                    ↓
        ┌────────────────────────────────────────────────────────┐
        │        Specialized Analysis Agents (Parallel)          │
        │                                                        │
        │  [Code Agent]           [Dependency Agent]             │
        │  [Configuration Agent]  [Test Agent]                   │
        │  [RAG Agent]            [Security Analysis Agent]      │
        └────────────────────────────────────────────────────────┘
                                    ↓
                            Finding Aggregation
                                    ↓
                               Critic Agent
                      (Validates / Rejects / Merges)
                                    ↓
                            Validated Findings
                                    ↓
                               Report Agent
                                    ↓
                         Structured Analysis Report
```

---

## 2. Specialized Agent Roster

### A. Orchestrator Flow (`DeploySafeAnalysisFlow`)
- **Role:** Central CrewAI-style orchestration engine.
- **Responsibilities:**
  - Ingests repository snapshots and builds the shared `AnalysisContext`.
  - Discovers files and categorizes repository artifacts.
  - Dynamically formulates an `AnalysisPlan` based on discovered technologies (e.g. Docker, Python, manifests).
  - Spawns independent specialized agents concurrently using a thread pool.
  - Feeds candidate findings into the Critic Agent and drives report generation.
- **Telemetry:** Records per-agent execution duration, tool invocations, and finding counts.

### B. Code Analysis Agent (`CodeAnalysisAgent`)
- **Role:** Source code and deployment hazard inspector.
- **Prompt:** `backend/app/agents/prompts/code_agent.md`
- **Focus Areas:**
  - Hardcoded local network endpoints (`http://localhost`, `127.0.0.1`) that fail upon containerization.
  - Dangerous exception handling (`except Exception: pass` swallowing errors).
  - Unsafe environment variable parsing and breaking API interfaces.
- **Evidence Contract:** Must cite exact file path and 1-indexed line numbers.
- **Tools:** `get_file_content`, `get_git_diff`, `code_check`.

### C. Dependency Agent (`DependencyAnalysisAgent`)
- **Role:** Software supply chain and package manifest inspector.
- **Prompt:** `backend/app/agents/prompts/dependency_agent.md`
- **Supported Manifests:** `requirements.txt`, `pyproject.toml`, `package.json`, `package-lock.json`, `go.mod`.
- **Focus Areas:**
  - Unpinned floating versions (e.g. `requests`, `fastapi>=0.100.0` without ceiling) risking non-reproducible CI builds.
  - Missing lockfiles in production deployments.
  - Deprecated or hazardous dependencies.
- **Tools:** `get_dependency_manifests`.

### D. Configuration Agent (`ConfigurationAnalysisAgent`)
- **Role:** Docker, compose, and environment configuration auditor.
- **Prompt:** `backend/app/agents/prompts/config_agent.md`
- **Focus Areas:**
  - Floating or unpinned container base images (e.g. `python:latest` or `node:alpine`).
  - Hardcoded local database URIs or network configurations in production settings.
  - Container privilege violations and insecure port mappings.
- **Tools:** `get_file_content`, `docker_check`.

### E. Test Agent (`TestAnalysisAgent`)
- **Role:** Test suite execution and regression coverage inspector.
- **Prompt:** `backend/app/agents/prompts/test_agent.md`
- **Core Principle:** Strictly distinguishes **OBSERVED** test failures from **INFERRED** missing regression tests.
  - **OBSERVED:** Safe pytest execution through sandboxed runner with actual captured failures.
  - **INFERRED:** Critical business/payment modules that lack corresponding `tests/test_*.py` files. Marked as `INFERRED` so Critic holds them for review.
- **Tools:** `run_tests_safe`, `get_test_files`.

### F. Documentation / RAG Agent (`DocumentationRAGAgent`)
- **Role:** Semantic vector search and cross-document policy correlation.
- **Prompt:** `backend/app/agents/prompts/rag_agent.md`
- **Mechanism:**
  - Queries Phase 2 Chroma vector database for deployment instructions and environment prerequisites.
  - Extracts mandatory variables (e.g. `REDIS_URL`, `DATABASE_URL`) from `README.md` or architecture docs.
  - Cross-examines `docker-compose.yml` or production configs to verify variables are supplied.
  - Discovers drift between documented expectations and actual container configs.
- **Tools:** `search_repository_context`, `ChromaRetriever`.

### G. Security Analysis Agent (`SecurityAnalysisAgent`)
- **Role:** Static analysis and credential exposure detector.
- **Prompt:** `backend/app/agents/prompts/security_agent.md`
- **Tools:** `run_security_scan`, `BanditScanner`, `SecretScanner`.
- **Secret Redaction:** Automatically detects high-entropy tokens, passwords, and API keys, masking them in evidence as `***REDACTED_SECRET***`. Never emits raw secrets into context or logs.

### H. Critic Agent (`CriticAgent`)
- **Role:** Ground-truth gatekeeper, anti-hallucination filter, and deduplicator.
- **Prompt:** `backend/app/agents/prompts/critic_agent.md`
- **Audit Verification Process:**
  1. **File Grounding:** Verifies that cited `file_path` physically exists in the repository. If not, the finding is **REJECTED** as a hallucination.
  2. **Evidence Substantiality:** Verifies that snippet contains concrete text, not empty placeholders.
  3. **Duplicate Detection:** Compares file paths, overlapping line ranges, and category hashes. Marks secondary instances as **DUPLICATE** and links to primary finding ID.
  4. **Status Assignment:**
     - `VALIDATED`: Supported by deterministic code or RAG evidence.
     - `NEEDS_REVIEW`: Inferred concerns (e.g. missing tests) requiring human engineer judgment.
     - `DUPLICATE`: Redundant finding merged into primary issue.
     - `REJECTED`: Hallucinated file or invalid evidence.
     - `INSUFFICIENT_EVIDENCE`: Lacks supporting ground truth.

### I. Report Synthesis Agent (`ReportGenerationAgent`)
- **Role:** Executive summary and metric compiler.
- **Prompt:** `backend/app/agents/prompts/report_agent.md`
- **Output:** Structured `AnalysisReport` containing real severity counts, prioritized recommendations, and agent execution audit trails.

---

## 3. Anti-Hallucination & Security Defenses

1. **Untrusted Data Boundary:** All repository contents and documentation snippets are wrapped in explicit untrusted delimiters:
   ```
   === UNTRUSTED REPOSITORY DATA BEGIN ===
   ... repository contents ...
   === UNTRUSTED REPOSITORY DATA END ===
   ```
   Prompts instruct LLMs that repository contents cannot override system instructions or issue commands.
2. **Deterministic File Verification:** Critic Agent runs physical filesystem checks before validating any finding.
3. **Secret Redaction:** Regex and entropy scanners sanitize credentials before evidence objects are created.
4. **Structured Schemas:** Every agent emits Pydantic-validated models; malformed JSON is rejected.

---

## 4. Failure Handling & Resilience

- **Individual Agent Failure:** If an agent encounters an exception, its state is marked `FAILED` with the captured error message; other agents continue unobstructed.
- **Critic Fallback:** If the Critic Agent fails, candidate findings remain in `NEEDS_REVIEW` rather than falsely asserting `VALIDATED`.
- **Provider Fallback:** LLM provider abstraction supports primary (Gemini/Groq) and fallback diagnostic modes.

---

## 5. Phase 4 Risk Engine Integration

In Phase 4, agent outputs do **NOT** produce the final risk score. Instead, findings flow through a multi-stage verification and scoring pipeline:

```
[Specialized Agents]
         ↓
  Candidate Findings
         ↓
   [Critic Agent]  ──> Anti-hallucination & physical file grounding
         ↓
 [Deduplication]   ──> Multi-agent clustering & canonical election
         ↓
 [Validated Set]   ──> Validated findings with ground truth
         ↓
  [Risk Engine]    ──> Deterministic formula: min(100, sum(w * conf * impact))
         ↓
 [Analysis Report] ──> Executive summaries, UI dashboards, & exports
```

1. **Critic Grounding:** Checks physical files and rejects non-existent paths.
2. **Finding Deduplication (`FindingDeduplicationService`):** Combines overlapping line ranges and rule IDs across agents (e.g. Code Agent and Security Agent both citing Dockerfile or compose). Merges reporting agents without losing attribution.
3. **Deterministic Scoring (`RiskEngine`):** Applies mathematical formula with project-defined severity weights (35, 25, 15, 7) and confidence multipliers (1.0, 0.8, 0.6). Excludes duplicate or rejected items with audit reasons.
4. **Authoritative Single Source:** The exact same score and breakdown appear across API, Overview Dashboard, Run Details, and exportable reports.

