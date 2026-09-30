# DeploySafe Phase 3 Midterm Demonstration Guide

## 1. Demo Objective
Demonstrate that DeploySafe is a real multi-agent deployment-risk intelligence platform—not a simple ChatGPT wrapper or mock UI. The demo shows autonomous agent specialization, dynamic planning, typed tool usage, repository RAG retrieval, cross-agent correlation, anti-hallucination Critic validation, and clean evidence presentation.

---

## 2. Live Demo Walkthrough (Step-by-Step)

### Step 1: Open DeploySafe
1. Ensure FastAPI backend is running on `http://127.0.0.1:8000`.
2. Ensure Vite frontend is running on `http://127.0.0.1:5173`.
3. Open `http://localhost:5173` in your browser.

### Step 2: Navigate to Multi-Agent Analysis
1. In the sidebar, click the **"Analyze"** tab (`/analyze`).
2. Notice the repository configuration panel:
   - Target repository input defaults to or click **"Load Demo Repo"** (`demo-repos/deploysafe-analysis-demo`).
   - Branch: `main`.
   - Commit: `HEAD`.
   - Scope: Code, Dependencies, Configuration, Tests, RAG Context, Secrets.

### Step 3: Trigger the Analysis Flow
1. Click **"Run Deployment Analysis"**.
2. Observe the flow state transition:
   `PREPARING` → `PLANNING` → `RUNNING_AGENTS` → `AGGREGATING` → `CRITIC_REVIEW` → `FINALIZING` → `COMPLETED`.

### Step 4: Explain the Autonomous Agent Activity Timeline
Point to the **"Autonomous Agent Activity & Telemetry"** grid on screen:
- **Code Analysis Agent:** Ran `get_file_content` and detected hardcoded `http://localhost:8080` endpoint in `src/payment.py:L9`.
- **Dependency Agent:** Parsed `requirements.txt` via `get_dependency_manifests` and identified unpinned `requests`.
- **Configuration Agent:** Audited `Dockerfile` and flagged unpinned `python:latest` image tag.
- **Test Agent:** Executed sandboxed pytest and flagged **INFERRED** missing regression test for payment processing.
- **Documentation / RAG Agent:** Queried Chroma vector database, discovered that `README.md` requires `REDIS_URL`, and detected its absence in `docker-compose.yml`.
- **Security Analysis Agent:** Scanned with credential detector and discovered hardcoded database URI, automatically applying `***REDACTED_SECRET***`.
- **Critic Agent:** Ran ground-truth validation across all candidate findings. Verified files exist, merged duplicate RAG findings, and retained inferred test concerns as `NEEDS_REVIEW`.
- **Report Agent:** Synthesized executive report and compiled exact severity counts.

### Step 5: Inspect Findings & Critic Decisions
Show the findings table:
- **Critical Severity:** Hardcoded database secret in `config/production.py:L5` (`VALIDATED`).
- **High Severity:** Hardcoded localhost endpoint in `src/payment.py:L9` (`VALIDATED`).
- **High Severity:** Unpinned base image `python:latest` in `Dockerfile:L1` (`VALIDATED`).
- **High Severity:** Unpinned dependency `requests` in `requirements.txt:L4` (`VALIDATED`).
- **High Severity:** Missing documented `REDIS_URL` in `docker-compose.yml` (`VALIDATED`).
- **High Severity:** Missing payment regression test in `src/payment.py` (`NEEDS_REVIEW` by Critic).

### Step 6: Open Finding Detail & Code Evidence Viewer
1. Click **"View Evidence"** on the hardcoded localhost finding (`F-CODE-001`).
2. Show the modal:
   - **Executive Summary:** Explains how localhost endpoints fail when deployed to container networks.
   - **Deployment Impact:** Container communication timeouts in production staging.
   - **Recommendation:** Refactor endpoint to consume environment variable `PAYMENT_GATEWAY_URL`.
   - **Agent Attribution:** Detected by `CodeAgent`, audited by `CriticAgent`.
   - **Code Evidence:** Shows exact line `L9-9` with snippet:
     `GATEWAY_URL = "http://localhost:8080/v1/charge"`
   - Click **"Copy Snippet"** to demonstrate clipboard integration.

---

## 3. Viva / Presentation Q&A Cheat Sheet

| Question | Strong Answer |
| :--- | :--- |
| **Why multiple agents instead of one large LLM prompt?** | A single LLM prompt suffers from context dilution, hallucination, and lack of separation of concerns. DeploySafe separates tasks into specialized domain agents (Code, Dependency, Config, Test, RAG, Security) each armed with deterministic tools, then subjects all findings to an adversarial Critic gatekeeper. |
| **How does DeploySafe prevent hallucination?** | The Critic Agent physically verifies that every cited file exists on disk, that line numbers correspond to real code, and that evidence is non-empty. Unsupported findings are marked `REJECTED` and removed from validated results. |
| **Where does RAG fit in?** | The Documentation / RAG Agent queries indexed repository documentation in the Chroma vector store. It extracts documented deployment requirements (e.g. `REDIS_URL`) and correlates them with configuration manifests (`docker-compose.yml`) to detect configuration drift. |
| **How are secrets protected?** | The Security Agent and File Discovery layer use regex and entropy detectors to sanitize passwords and API keys, replacing them with `***REDACTED_SECRET***`. Raw secrets are never sent to external LLMs or logged. |
| **Are commands executed safely?** | Yes. `SafeCommandExecutor` enforces a strict binary allowlist (`git`, `pytest`, `python`, etc.), runs without shell interpolation (`shell=False`), restricts execution to the repo root, enforces a 30s timeout, and caps output at 100 KB. |
| **Why is there no 0–100 risk score yet?** | As per the project PRD, Phase 3 strictly implements the multi-agent intelligence layer, evidence collection, and Critic validation. The deterministic mathematical scoring engine belongs to Phase 4. |
