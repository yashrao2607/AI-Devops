# DeploySafe — Midterm Live Demonstration Script (v2)

> **Course:** Agentic AI (CSE3101)  
> **Target Repository:** `demo-repos/deploysafe-analysis-demo`  
> **Duration:** 3–5 Minutes Live Walkthrough  
> **UI URL:** `http://localhost:5173/`  
> **API URL:** `http://127.0.0.1:8000/`

---

## 1. Pre-Flight Verification (30 Seconds Before Demo)

Run these two quick commands in your terminal to ensure services are responsive:

```powershell
# 1. Verify backend health
curl http://127.0.0.1:8000/api/v1/health

# Expected response:
# {"status":"healthy","app_name":"DeploySafe","version":"0.1.0",...}
```

```powershell
# 2. Verify all 62 unit and integration tests are passing
python -m pytest backend/tests -q
# Expected: 62 passed in ~6.8s
```

Open the web browser to:
```text
http://localhost:5173/
```

---

## 2. Six-Step Live Demonstration Walkthrough

### Step 1: Open DeploySafe Web Console
- **Action:** Open `http://localhost:5173/`.
- **What to say:**
  > "Professor, here is the live DeploySafe web console. On the left navigation, you can see our key views: Overview Dashboard, Analyze Pipeline, Repositories, Runs, Findings Directory, Agents, and Deployment Reports. Notice in the top status bar that our FastAPI backend is connected, our target repository is set to our local evaluation repo, and the system is healthy."

---

### Step 2: Trigger Multi-Agent Analysis
- **Action:** Click **"Analyze"** in the sidebar (or navigate to `/analyze`).
- **Target Repository Path:** `demo-repos/deploysafe-analysis-demo`
- **Branch:** `main`
- **Action:** Click the green **"Run Deployment Analysis"** button.
- **What to say:**
  > "We now trigger an end-to-end deployment analysis. The Orchestrator immediately discovers the repository's technology stack (Python, Docker, Docker Compose) and dispatches our specialized domain agents in parallel."
  > "In the live telemetry timeline, you can see each agent executing: Code Agent, Config Agent, Dependency Agent, Test Agent, Documentation RAG Agent, and Security Agent."

---

### Step 3: Inspect Vector RAG Context Retrieval
- **Action:** Point out the Documentation/RAG agent output in the telemetry list or on the dashboard.
- **What to say:**
  > "Notice how the Documentation RAG agent queries ChromaDB. It indexes `README.md` and discovers that our application requires an external Redis cache service (`REDIS_URL`). This architectural intent is passed directly to the Config Agent."

---

### Step 4: Examine Critic Validation & Deduplication
- **Action:** Navigate to **"Findings"** (`/findings`).
- **What to say:**
  > "Here in the Findings Directory, we see 8 candidate issues evaluated. 6 were validated by the Critic agent with exact source line citations, 1 was flagged for human review, and 1 duplicate finding was merged."
  > "The Critic agent physically inspected `docker-compose.yml` on disk, verified that Redis is missing from the service definition, and confirmed this is a High-severity crash risk. It also verified hardcoded secrets and unpinned container tags."

---

### Step 5: Review Deterministic Risk Score
- **Action:** Click **"Overview"** (`/overview`).
- **What to say:**
  > "On our Overview Dashboard, the Risk Engine calculates an overall Deployment Risk Score of **100 / 100 (CRITICAL RISK)**."
  > "We want to highlight that this score is calculated deterministically by pure Python arithmetic—not by an LLM guessing a number. Each Critic-validated Critical finding adds 35 points, each High finding adds 25 points, scaled by confidence factors and clamped between 0 and 100."

---

### Step 6: Export Multi-Format Deployment Report
- **Action:** Click **"Reports"** in the sidebar (`/reports`).
- **Action:** Switch between **HTML**, **Markdown**, and **JSON** tabs.
- **What to say:**
  > "Finally, DeploySafe generates an auditable Deployment Readiness Report. Engineers can view the rendered HTML summary, copy Markdown into release tickets, or export structured JSON for integration with other tooling."
  > "This concludes our live demonstration of DeploySafe Phases 1 through 4."

---

## 3. Contingency / Offline Mode

If classroom Wi-Fi is unstable:
- DeploySafe runs 100% locally with zero external network calls.
- The active provider is currently set to `diagnostic_mock` with local persistent ChromaDB storage and SQLite, guaranteeing a 100% stable live demo without API timeout or rate limit risks.
