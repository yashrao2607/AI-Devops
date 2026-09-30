# DeploySafe

> **Know the deployment risk before you deploy.**

DeploySafe is a multi-agent AI deployment-readiness intelligence platform. It analyzes software repositories and proposed pull requests, combining deterministic scanners with multi-agent LLM reasoning (via CrewAI) and repository RAG (via Chroma) to calculate explainable, evidence-backed deployment-risk assessments.

---

## Current Status: Phase 3 — Core Multi-Agent DeploySafe

Phase 3 implements the autonomous multi-agent intelligence layer coordinating 8 specialized agents, dynamic orchestrator planning, typed deterministic tools, RAG repository cross-correlation, and an adversarial Critic validation gatekeeper:
- **Orchestrator Flow:** Dynamically formulates an `AnalysisPlan` based on discovered technologies and executes independent agents concurrently in a thread pool.
- **Specialized Domain Agents:**
  - `CodeAnalysisAgent`: Detects hardcoded localhost/dev endpoints, unhandled exceptions, and deployment hazards.
  - `DependencyAnalysisAgent`: Parses package manifests (`requirements.txt`, `package.json`, etc.) to flag unpinned versions and missing lockfiles.
  - `ConfigurationAnalysisAgent`: Inspects Dockerfiles and compose manifests for unpinned base images and configuration drift.
  - `TestAnalysisAgent`: Safely executes sandboxed pytest runners and strictly distinguishes OBSERVED failures from INFERRED test coverage.
  - `DocumentationRAGAgent`: Queries Chroma vector store, cross-correlating documented requirements (e.g. `REDIS_URL`) against actual deployment manifests.
  - `SecurityAnalysisAgent`: Combines static analysis and credential detection with automatic secret masking (`***REDACTED_SECRET***`).
- **Critic Agent Gatekeeper:** Adversarial verification enforcing physical file existence on disk, checking line numbers, merging duplicates, and guarding against LLM hallucinations.
- **Report Synthesis Agent:** Aggregates audited findings and compiles real severity counts without fake risk scores.
- **Full Web UI:** Interactive React analysis console with live agent execution timeline, severity summary cards, filterable findings table, and line-accurate code evidence viewer.

---

## Quick Start

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 2. Environment Configuration
Copy the configuration template and review the setup instructions:
```powershell
cp .env.example .env
```
Follow the detailed guide in [ENV_SETUP.md](file:///d:/NAVEEN-SIR_PROJECT/ENV_SETUP.md) to add your API keys when ready (the platform runs in safe diagnostic/mock mode without them).

### 3. Check Real-Time Project Progress
You can monitor the implementation status of all parallel workstreams directly in your terminal at any time:
```powershell
python scripts/status.py
```

### 4. Running the Backend
```powershell
uvicorn backend.app.main:app --reload --reload-dir backend --port 8000
```
Backend API will be live at: `http://localhost:8000`  
Interactive Swagger API docs: `http://localhost:8000/docs`  
Health check endpoint: `http://localhost:8000/api/v1/health`

### 5. Running the Frontend
```powershell
cd frontend
npm install
npm run dev
```
Frontend development server will open at: `http://localhost:5173`

### 6. Ingest & Query the Demo Repository via CLI
```powershell
python scripts/verify_rag_live.py
```

### 7. Running the Test Suite
```powershell
python -m pytest backend/tests -v
```

---

## Documentation Links
- [Product Requirements Document (PRD)](file:///d:/NAVEEN-SIR_PROJECT/prd.md)
- [Phase 3 Multi-Agent Architecture & Roster](file:///d:/NAVEEN-SIR_PROJECT/docs/agents.md)
- [Phase 3 Typed Tool Layer & Security Sandbox](file:///d:/NAVEEN-SIR_PROJECT/docs/tools.md)
- [Phase 3 Midterm Demonstration Guide](file:///d:/NAVEEN-SIR_PROJECT/docs/phase3-demo.md)
- [Phase 2 RAG Architecture Specification](file:///d:/NAVEEN-SIR_PROJECT/docs/rag.md)
- [System Architecture & Diagrams](file:///d:/NAVEEN-SIR_PROJECT/docs/architecture.md)
- [API Key & Environment Setup Guide](file:///d:/NAVEEN-SIR_PROJECT/ENV_SETUP.md)
- [Phase 1 Completion Report](file:///d:/NAVEEN-SIR_PROJECT/PHASE1DONE.md)
- [Phase 2 Completion Report](file:///d:/NAVEEN-SIR_PROJECT/PHASE2DONE.md)
- [Phase 3 Completion Report](file:///d:/NAVEEN-SIR_PROJECT/PHASE3DONE.md)
