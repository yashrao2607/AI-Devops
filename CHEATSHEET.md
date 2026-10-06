# 🛡️ DeploySafe — Complete Project & Docker Runbook Cheat Sheet

> **DeploySafe** is a production-grade, multi-agent AI deployment-risk analysis platform that audits source code, dependency manifests, CI/CD workflows, Docker configs, and regression tests to prevent disastrous production deployments.

---

## 📑 Table of Contents
1. [⚡ Quick Start: 1-Command Launchers](#-quick-start-1-command-launchers)
2. [🐳 Docker Container Commands](#-docker-container-commands)
3. [💻 Native Local Development Commands (Without Docker)](#-native-local-development-commands-without-docker)
4. [🔑 Environment Configuration (`.env`)](#-environment-configuration-env)
5. [📡 Essential API Endpoints & cURL Cheat Sheet](#-essential-api-endpoints--curl-cheat-sheet)
6. [🧪 Automated Testing & Verification Commands](#-automated-testing--verification-commands)
7. [🛠️ Troubleshooting & Frequently Asked Questions](#️-troubleshooting--frequently-asked-questions)

---

## ⚡ Quick Start: 1-Command Launchers

### Option A: Run via Docker (Recommended for Isolated Deployment)
```powershell
# In PowerShell:
.\scripts\docker_run.ps1
```
*Or directly via Docker Compose:*
```bash
docker compose up --build -d
```

### Option B: Run Natively on Windows Host
```powershell
# In PowerShell:
.\scripts\run_local.ps1
```

Once running:
- **Frontend Web Dashboard**: [`http://localhost:5173`](http://localhost:5173) (or `http://localhost:3000`)
- **Backend API Server**: [`http://127.0.0.1:8000`](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)
- **Health Check**: [`http://127.0.0.1:8000/api/v1/health`](http://127.0.0.1:8000/api/v1/health)

---

## 🐳 Docker Container Commands

DeploySafe includes production-grade containerization with multi-stage builds, non-root security, persistent volumes, and reverse proxying.

### 1. Build and Start All Containers (Detached Mode)
```bash
docker compose up --build -d
```

### 2. View Live Aggregated Logs
```bash
docker compose logs -f
```

### 3. View Logs for a Specific Service
```bash
# Backend logs
docker compose logs -f backend

# Frontend Nginx logs
docker compose logs -f frontend
```

### 4. Check Container Status and Health
```bash
docker compose ps
```

### 5. Stop Containers (Preserving Data Volumes)
```bash
docker compose down
```

### 6. Stop Containers and Wipe All Persistent Data (Chroma & Cloned Repos)
```bash
docker compose down -v
```

### 7. Rebuild From Scratch (No Cache)
```bash
docker compose build --no-cache
docker compose up -d
```

### 8. Execute an Interactive Shell Inside the Backend Container
```bash
docker compose exec backend bash
# Inside container:
git --version
python -c "import chromadb; print(chromadb.__version__)"
exit
```

### 9. Development Mode with Hot-Reloading
```bash
docker compose -f docker-compose.dev.yml up --build
```

---

## 💻 Native Local Development Commands (Without Docker)

### 1. Backend Setup & Run

#### Step 1: Install Python Dependencies
```bash
pip install -r backend/requirements.txt
```

#### Step 2: Start the FastAPI Backend Server
```bash
# Standard run
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# Run with hot-reloading enabled for code changes:
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup & Run

#### Step 1: Navigate to the Frontend Directory
```bash
cd frontend
```

#### Step 2: Install Node Dependencies
```bash
npm install
```

#### Step 3: Start Vite Development Server
```bash
npm run dev
```

#### Step 4: Build Frontend for Production (Optional)
```bash
npm run build
```

---

## 🔑 Environment Configuration (`.env`)

Place your `.env` file in the repository root directory. The application automatically loads these variables.

```ini
# ==============================================================================
# LLM Providers Configuration
# ==============================================================================
# Primary LLM provider: 'groq' (ultra-fast) or 'gemini'
PRIMARY_LLM_PROVIDER=groq
FALLBACK_LLM_PROVIDER=gemini

# Groq API Configuration (Free tier: console.groq.com)
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

# Google Gemini API Configuration (aistudio.google.com)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Optional GitHub Personal Access Token for private repo ingestion
GITHUB_TOKEN=

# ==============================================================================
# Persistence & Application Settings
# ==============================================================================
DATABASE_URL=sqlite:///./deploysafe.db
CHROMA_PATH=./chroma_db

APP_ENV=development
LOG_LEVEL=INFO

API_PORT=8000
API_HOST=0.0.0.0
FRONTEND_URL=http://localhost:5173
```

---

## 📡 Essential API Endpoints & cURL Cheat Sheet

You can test any part of the system directly using terminal cURL commands.

### 1. Health & LLM Status Check
```bash
curl -X GET http://127.0.0.1:8000/api/v1/health
```
*Sample Response:*
```json
{
  "status": "healthy",
  "app_name": "DeploySafe",
  "version": "0.1.0",
  "active_llm_provider": "groq",
  "gemini_configured": true,
  "groq_configured": true,
  "database_status": "connected"
}
```

### 2. List Available Repositories
```bash
curl -X GET http://127.0.0.1:8000/api/v1/repositories
```

### 3. Ingest a GitHub Repository
```bash
curl -X POST http://127.0.0.1:8000/api/v1/repositories/ingest \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/yashrao2607/web-scrape", "branch": "main"}'
```

### 4. Trigger Full Multi-Agent Deployment Risk Analysis
```bash
# Analyze any GitHub repository or local snapshot:
curl -X POST http://127.0.0.1:8000/api/v1/analysis/run \
  -H "Content-Type: application/json" \
  -d '{
    "repository_id": "yashrao2607/web-scrape",
    "branch": "main",
    "mode": "quick"
  }'
```

### 5. Fetch Latest Analysis Report (Executive Brief & Risk Score)
```bash
curl -X GET http://127.0.0.1:8000/api/v1/analysis/latest/report
```

### 6. Get Historical Runs Summary
```bash
curl -X GET http://127.0.0.1:8000/api/v1/runs
```

### 7. Filter Validated Findings (Critical / High)
```bash
# Filter all CRITICAL findings:
curl -X GET "http://127.0.0.1:8000/api/v1/findings?severity=CRITICAL"

# Filter by Status (VALIDATED):
curl -X GET "http://127.0.0.1:8000/api/v1/findings?status=VALIDATED"
```

### 8. Download HTML or Markdown Deployment Risk Report
```bash
# Get HTML Report for a specific run ID:
curl -X GET "http://127.0.0.1:8000/api/v1/runs/YOUR_RUN_ID/report?format=html" -o report.html

# Get Markdown Report:
curl -X GET "http://127.0.0.1:8000/api/v1/runs/YOUR_RUN_ID/report?format=markdown" -o report.md
```

---

## 🧪 Automated Testing & Verification Commands

### 1. Run End-to-End Pipeline Verification Script
```bash
python verify_pipelines.py
```
*Validates:*
- Multi-agent orchestration (Code, Config, Test, Dependency, RAG, Security, Critic, Report).
- Live Groq LLM executive intelligence synthesis.
- Exact line numbers and ground-truth code snippet evidence.
- Deterministic 0–100 risk calculation.

### 2. Run Multi-Repository Benchmark
```bash
python test_4_repos.py
```

### 3. Run Backend Unit & Integration Tests (Pytest)
```bash
pytest backend/tests -v
```

---

## 🛠️ Troubleshooting & Frequently Asked Questions

### Q1: "Port 8000 or 5173 is already in use"
Run this quick PowerShell one-liner to free the ports:
```powershell
Get-NetTCPConnection -LocalPort 8000, 5173 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
```

### Q2: "Docker Desktop daemon is not running"
1. Open **Docker Desktop** from your Windows Start Menu.
2. Wait for the whale icon in the Windows taskbar system tray to turn solid green ("Engine running").
3. Run `docker compose up -d`.

### Q3: "Groq Rate Limit Exceeded (429)"
DeploySafe features **automatic resilience**:
- Primary model is set to **`openai/gpt-oss-120b`**, which has high token-per-minute limits.
- If a rate limit is ever reached, DeploySafe automatically falls back to **`openai/gpt-oss-20b`** and **`gemini-2.5-flash`**.

### Q4: "How do I reset Chroma Vector DB and Database?"
Simply delete the local folders or run:
```bash
# For local run:
rm -rf chroma_db deploysafe.db

# For Docker run:
docker compose down -v
```
Upon the next run, the SQLite schema and Chroma vector collections will be automatically recreated.
