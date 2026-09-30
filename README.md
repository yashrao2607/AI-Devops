# DeploySafe

> **Know the deployment risk before you deploy.**

DeploySafe is a multi-agent AI deployment-readiness intelligence platform. It analyzes software repositories and proposed pull requests, combining deterministic scanners with multi-agent LLM reasoning (via CrewAI) and repository RAG (via Chroma) to calculate explainable, evidence-backed deployment-risk assessments.

---

## Current Status: Phase 2 — Repository Analysis + RAG Foundation

Phase 2 introduces deep repository ingestion, AST/semantic chunking, Chroma vector storage, and verifiable RAG knowledge retrieval:
- **Repository Ingestion:** Ingest local repository directories, remote GitHub repositories, and uploaded ZIP archives with Zip-Slip path traversal defense and quota enforcement.
- **File Discovery & Secret Redaction:** Recursively scans repositories, categorizing files into 8 structural domains (`SOURCE_CODE`, `TEST`, `CONFIG`, `DOCUMENTATION`, `DOCKER`, `CI_CD`, `SCRIPT`, `OTHER`), applying ignore rules and redacting secrets (`***REDACTED_SECRET***`).
- **Semantic Chunking:** Splits along classes, functions, markdown headings, and docker instruction boundaries with exact source line boundaries (`line_start`, `line_end`) and deterministic hashes.
- **Embedding Abstraction:** Primary Gemini `text-embedding-004` (768 dimensions) with deterministic fallback `LocalEmbeddingProvider` (384 dimensions).
- **Chroma Vector Store:** Isolated collections per repository (`CHROMA_PATH`), enforcing strict data isolation and in-memory testing mode.
- **RAG Retrieval Engine:** Semantic vector search with anti-hallucination thresholding (`FOUND`, `LOW_RELEVANCE`, `NOT_FOUND`).
- **Interactive UI:** Connected frontend page for repository ingestion, real-time pipeline telemetry, discovered files browser, and code evidence viewer with copyable snippets.

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
- [Phase 2 RAG Architecture Specification](file:///d:/NAVEEN-SIR_PROJECT/docs/rag.md)
- [System Architecture & Diagrams](file:///d:/NAVEEN-SIR_PROJECT/docs/architecture.md)
- [API Key & Environment Setup Guide](file:///d:/NAVEEN-SIR_PROJECT/ENV_SETUP.md)
- [Phase 1 Completion Report](file:///d:/NAVEEN-SIR_PROJECT/PHASE1DONE.md)
- [Phase 2 Completion Report](file:///d:/NAVEEN-SIR_PROJECT/PHASE2DONE.md)
