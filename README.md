# DeploySafe

> **Know the deployment risk before you deploy.**

DeploySafe is a multi-agent AI deployment-readiness intelligence platform. It analyzes software repositories and proposed pull requests, combining deterministic scanners with multi-agent LLM reasoning (via CrewAI) and repository RAG (via Chroma) to calculate explainable, evidence-backed deployment-risk assessments.

---

## Current Status: Phase 1 — Foundation & Setup

Phase 1 provides the core foundation of the DeploySafe platform:
- **FastAPI Backend:** Modular API with health diagnostics, database initialization (SQLite), structured logging, and secret masking.
- **Frontend App Shell:** Modern developer-security platform interface built with React, TypeScript, and Tailwind CSS.
- **LLM Abstraction Layer:** Unified `LLMProvider` interface supporting Google Gemini (primary) and Groq Cloud (fallback) with structured output and graceful missing-key handling.
- **CrewAI Flow Foundation:** Minimal real CrewAI Flow and readiness agent executing structured Pydantic evaluations.
- **Testing & Verification:** Comprehensive pytest test suite for backend, configuration, LLM abstraction, and CrewAI workflows.

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
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
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

### 6. Running Tests
```powershell
pytest backend/tests -v
```

---

## Documentation Links
- [Product Requirements Document (PRD)](file:///d:/NAVEEN-SIR_PROJECT/prd.md)
- [Product Scope & Roadmap](file:///d:/NAVEEN-SIR_PROJECT/docs/product-scope.md)
- [System Architecture & Diagrams](file:///d:/NAVEEN-SIR_PROJECT/docs/architecture.md)
- [API Key & Environment Setup Guide](file:///d:/NAVEEN-SIR_PROJECT/ENV_SETUP.md)
- [Phase 1 Completion Report](file:///d:/NAVEEN-SIR_PROJECT/PHASE1DONE.md)
