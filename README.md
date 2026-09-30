# DeploySafe

> **Know the deployment risk before you deploy.**

DeploySafe is a multi-agent AI deployment-readiness intelligence platform. It analyzes software repositories and proposed pull requests, combining deterministic scanners with multi-agent LLM reasoning (via CrewAI) and repository RAG (via Chroma) to calculate explainable, evidence-backed deployment-risk assessments.

---

## Current Status: Phase 4 — Risk Engine + Professional Product UI

Phase 4 transforms the working multi-agent analysis system into a production-grade deployment-risk platform featuring mathematical risk scoring, finding lifecycle management, and a polished developer UI:
- **Deterministic Risk Engine (`RiskEngine`):** Computes bounded 0–100 scores via mathematical weighting (Critical=35, High=25, Medium=15, Low=7) adjusted by confidence and impact multipliers. LLMs never directly generate the final score.
- **Finding Deduplication (`FindingDeduplicationService`):** Multi-attribute clustering across files, line ranges, categories, and scanner rules, merging duplicate agent discoveries while preserving attribution.
- **Auditable Status Lifecycle:** Findings progress through strictly governed states (`VALIDATED`, `NEEDS_REVIEW`, `DUPLICATE`, `REJECTED`, `INSUFFICIENT_EVIDENCE`, `DISMISSED`) with manual triage overrides that dynamically trigger score recalculations.
- **Production Developer Dashboard:**
  - **Overview Dashboard:** Risk Score Hero Gauge, mathematical breakdown modal ("How is this calculated?"), severity breakdown cards, top findings, and recent runs.
  - **Runs Console:** Chronological historical runs table, agent execution telemetry (duration, tools called, finding counts), and score contributor audits.
  - **Findings Directory:** Global searchable catalog with multi-attribute filters (Severity, Status, Agent) and inspect drawer with code evidence and actionable remediation.
  - **Reports & Exports:** Interactive multi-format preview with instant downloads (standalone styled HTML, documentation Markdown, and structured JSON).
- **Multi-Format Report Service:** Generates self-contained styled HTML documents, clean Markdown reports, and JSON API payloads for CI/CD gates.

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
- [Phase 4 Deterministic Risk Model & Formula](file:///d:/NAVEEN-SIR_PROJECT/docs/risk-model.md)
- [Phase 4 Live Demonstration & Viva Guide](file:///d:/NAVEEN-SIR_PROJECT/docs/phase4-demo.md)
- [Phase 3 Multi-Agent Architecture & Roster](file:///d:/NAVEEN-SIR_PROJECT/docs/agents.md)
- [Phase 3 Typed Tool Layer & Security Sandbox](file:///d:/NAVEEN-SIR_PROJECT/docs/tools.md)
- [Phase 3 Midterm Demonstration Guide](file:///d:/NAVEEN-SIR_PROJECT/docs/phase3-demo.md)
- [Phase 2 RAG Architecture Specification](file:///d:/NAVEEN-SIR_PROJECT/docs/rag.md)
- [System Architecture & Diagrams](file:///d:/NAVEEN-SIR_PROJECT/docs/architecture.md)
- [API Key & Environment Setup Guide](file:///d:/NAVEEN-SIR_PROJECT/ENV_SETUP.md)
- [Phase 1 Completion Report](file:///d:/NAVEEN-SIR_PROJECT/PHASE1DONE.md)
- [Phase 2 Completion Report](file:///d:/NAVEEN-SIR_PROJECT/PHASE2DONE.md)
- [Phase 3 Completion Report](file:///d:/NAVEEN-SIR_PROJECT/PHASE3DONE.md)
- [Phase 4 Completion Report](file:///d:/NAVEEN-SIR_PROJECT/PHASE4DONE.md)
