# DeploySafe — Project Contribution Matrix

> **Project**: DeploySafe (Agentic AI Pre-Deployment Risk Platform)  
> **Course Mentors**: Mr. Naveen Singla & Dr. Kiran Khatter  
> **Release**: v1.0.0 Production Release

---

### Executive Overview
DeploySafe was architected and built through a cross-functional engineering approach. Every team member developed deep competence across multiple tiers of the system (Agentic AI, Backend Engineering, Deterministic Mathematics, Frontend UX, and DevOps).

---

### Component Responsibility Breakdown

| System Component | Primary Module / Directory | Key Responsibilities & Contributions |
| :--- | :--- | :--- |
| **Frontend Architecture & UX** | `frontend/src/` | React 18 + Vite SPA design, dark-mode design system, TailwindCSS styling, live telemetry visualizers, formula explainability modal, Before/After run comparison view, code evidence viewer. |
| **Backend API & Service Layer** | `backend/app/api/v1/`, `backend/app/main.py` | FastAPI server design, REST endpoints (`/runs`, `/compare`, `/findings`, `/health`, `/evaluation`, `/observability`), database session management, global exception handling, CORS policies. |
| **Multi-Agent Architecture** | `backend/app/agents/specialized/` | Code Agent, Dependency Agent, Config Agent, Test Agent, Security Agent, Report Agent design; role definitions, tool boundaries, and structured Pydantic schema outputs. |
| **Orchestration & Workflow** | `backend/app/agents/analysis_flow.py` | Multi-agent execution flow, dynamic planning (`AnalysisPlan`), thread pool concurrency, state transitions (`PREPARING` → `RUNNING_AGENTS` → `CRITIC_REVIEW` → `FINALIZING`), Partial Failure policy. |
| **RAG & Vector Retrieval** | `backend/app/services/rag/` | File discovery service, AST token categorization, text chunking (1000 char / 200 overlap), ChromaDB vector store integration, Gemini `text-embedding-004` & local deterministic fallback embeddings. |
| **Deterministic Tools** | `backend/app/services/tools/repo_tools.py` | Ground-truth code extraction (`get_file_content`), Git diff parsing (`get_git_diff`), Dockerfile security checks (`docker_check`), safe test harness (`run_tests_safe`), dependency manifest parsers. |
| **Critic & Reflection** | `backend/app/agents/specialized/critic_agent.py` | Adversarial auditor agent; ground-truth line and file existence validation, snippet corroboration, duplicate grouping, hallucination rejection engine. |
| **Deterministic Risk Engine** | `backend/app/services/risk_engine.py` | Mathematical scoring algorithm ($\text{Score} \in [0, 100]$), severity weighting (`CRITICAL`=35, `HIGH`=25, `MEDIUM`=15, `LOW`=7), confidence and impact calibration, explainable score ledger. |
| **Deployment Gate Policy** | `backend/app/services/gate_policy.py` | Deterministic deployment gating (`ALLOWED`, `REVIEW_REQUIRED`, `BLOCKED`), severity ceiling enforcement, override justification handling. |
| **GitHub & CI/CD Integration** | `backend/app/services/github_service.py`, `.github/workflows/` | GitHub API service, PR diff retrieval, idempotent PR commenting, DeploySafe CLI (`backend/app/cli.py`), GitHub Action workflow YAML, fork PR safety. |
| **Security & Safety Guardrails** | `backend/app/services/safety.py` | Secret redaction engine (`SecretRedactionEngine`), regex patterns (Gemini, Groq, GitHub PAT, AWS, RSA), prompt injection defenses (`<untrusted_repository_content>`), command permission policies. |
| **Observability & Tracing** | `backend/app/services/observability.py` | End-to-end trace collection (`AnalysisTrace`), timeline events, per-agent latency telemetry, tool execution logging, `/trace` and `/timeline` endpoints. |
| **Evaluation Benchmark Suite** | `backend/app/services/evaluator.py`, `demo-repos/evaluation/` | Benchmark framework, 5 evaluation repository fixtures, automated metric computation (Recall, Evidence Validity, Latency), `evaluation-report.json`. |
| **Docker & Packaging** | `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` | Multi-stage Docker builds, non-root user permissions (`USER appuser`), Nginx reverse proxy configuration, container health checks, compose orchestration. |
| **Quality Assurance & Testing** | `backend/tests/` | 92 comprehensive unit, integration, and security tests across Phases 1 through 6; 100% pass rate. |
| **Documentation & Viva Readiness** | `README.md`, `docs/` | System architecture guide, Viva defense guide (24 Q&As), 27-step demo script, presentation outline, environment setup manual. |

---

### Verification Proof
- All 92 automated tests run and verified via pytest (`pytest backend/tests/ -q`).
- Frontend production bundle cleanly built with 0 TypeScript errors (`npm --prefix frontend run build`).
- Git repository audited with zero committed secrets and complete `.gitignore` enforcement.
