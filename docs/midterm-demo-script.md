# DeploySafe — Midterm Live Demonstration Script & Step-by-Step Viva Guide

> **Course:** Agentic AI (CSE3101)  
> **Demonstration Target:** Seeded Demo Repository (`demo-repos/deploysafe-analysis-demo`)  
> **Target Audience:** Course Professor & Evaluation Panel

---

## 1. Pre-Demo Environment Verification

Before inviting the professor to observe the screen, ensure both backend and frontend processes are active:

```powershell
# Check backend health
curl http://127.0.0.1:8000/api/v1/health

# Output should show:
# {"status":"healthy","app_name":"DeploySafe","version":"0.1.0","active_llm_provider":"diagnostic_mock",...}
```

```powershell
# Run the automated test suite to prove full system integrity
python -m pytest backend/tests -v
# Output: 62 passed, 0 failures in ~6.8 seconds
```

Open Google Chrome or Microsoft Edge to:
```text
http://localhost:5173/
```

---

## 2. Seven-Step Demonstration Walkthrough

### Step 1: Platform Overview & Navigation Shell
1. Open `http://localhost:5173/` in your browser.
2. **What to say:**
   > "Professor, this is the DeploySafe web console. You can see our platform navigation on the left: Overview Dashboard, Analyze pipeline, Repositories, Runs history, Findings Directory, Agents, and Deployment Reports. Notice in the top status bar that our FastAPI gateway is connected, our target repository context is set, and our active provider status is displayed."

---

### Step 2: Overview Dashboard & Risk Score Hero
1. Focus the professor's attention on the **Deployment Risk Score Hero**:
   - **Risk Score:** `100 / 100`
   - **Risk Level Badge:** `CRITICAL RISK`
   - **Summary:** "Calculated deterministically from 6 Critic-validated findings. Zero LLM hallucination in mathematical scoring."
2. Point out the **Severity Breakdown Cards**:
   - **Critical:** 2 (Weight: 35.0 pts each)
   - **High:** 6 (Weight: 25.0 pts each)
   - **Medium:** 0
   - **Low:** 0
3. Point out the **Audit & Deduplication Health Banner**:
   - **Critic Validated:** 6
   - **Needs Review:** 1
   - **Duplicates Merged:** 1
   - **Rejected / Insufficient:** 0

---

### Step 3: Demonstrate Score Transparency ("How is this calculated?")
1. Click the blue link **"How is this calculated?"** next to the score hero.
2. In the modal that opens, show the evaluator the exact mathematical formula:
   $$\text{Score} = \min\left(100.0, \text{round}\left(\sum \text{weight} \times \text{confidence} \times \text{impact}\right)\right)$$
3. **What to say:**
   > "Notice that the LLM does not generate this score. Our `RiskEngine` calculates it strictly from validated findings using project-defined severity weights: Critical=35, High=25, Medium=15, Low=7. In this demo repo, 2 Critical (70 pts) plus 4 Validated High (100 pts) equals 170 raw points, which is normalized and bounded at 100.0 CRITICAL."
4. Close the modal.

---

### Step 4: Execute a Live Analysis Run
1. Click **"Analyze"** in the left sidebar navigation (`/analyze`).
2. Verify the pre-filled target:
   - **Repository Path:** `demo-repos/deploysafe-analysis-demo`
   - **Target Branch:** `main`
3. Click the green button: **"Run Deployment Analysis"**.
4. Point out the **Live Agent Activity & Telemetry Timeline**:
   - Watch the agent cards update live:
     - `Code Analysis Agent` (COMPLETED, duration ~0.01s, 1 finding)
     - `Dependency Agent` (COMPLETED, duration ~0.01s, 1 finding)
     - `Configuration Agent` (COMPLETED, duration ~0.01s, 1 finding)
     - `Test Agent` (COMPLETED, duration ~0.01s, 1 finding)
     - `Documentation / RAG Agent` (COMPLETED, duration ~0.02s, 2 findings)
     - `Security Analysis Agent` (COMPLETED, duration ~0.01s, 2 findings)
     - `Critic Validation Agent` (COMPLETED, 6 validated, 1 review, 1 duplicate)
     - `Report Synthesis Agent` (COMPLETED)
5. Show the **Deterministic Risk Score Banner** that appears above the severity cards upon completion.

---

### Step 5: Inspect Run History & Telemetry
1. Click **"Runs"** in the left navigation sidebar (`/runs`).
2. Show the historical runs table:
   - **Run ID:** `run_1588a4898a49`
   - **Target:** `deploysafe-analysis-demo • main`
   - **Risk Score:** `100/100 CRITICAL`
   - **Findings Breakdown:** `8 total, 6 validated, 1 review`
   - **Duration:** `1.44s`
3. Click **"Inspect"** on the run to open the Run Details drawer.
4. Show the professor:
   - **Active Score Contributors:** Every finding adding points (+35 pts, +25 pts).
   - **Excluded from Score Calculation:** `F-TST-001` excluded because it is an inferred concern in `NEEDS_REVIEW`; `F-RAG-002` excluded as a duplicate.
   - **Agent Execution Telemetry:** Exact runtime seconds and tools called for every agent.
5. Close the drawer.

---

### Step 6: Findings Directory, Evidence & Live Triage
1. Click **"Findings"** in the left navigation sidebar (`/findings`).
2. Test the **Search Input**:
   - Type `REDIS` -> Instantly filters to the documentation mismatch finding.
   - Type `password` or `secret` -> Instantly filters to hardcoded credentials.
   - Clear the search box.
3. Test the **Severity & Status Filter Pills**:
   - Click `CRITICAL` -> Filters to the 2 hardcoded database credentials.
   - Click `NEEDS_REVIEW` -> Filters to `F-TST-001` (missing payment tests).
   - Click `ALL` to restore the full catalog.
4. Click **"Inspect"** on finding `F-SEC-002`:
   - Point out the answers to the 5 core developer questions:
     - **WHAT:** "Potential Hardcoded Secret: DATABASE_URI_WITH_CREDS"
     - **WHY / IMPACT:** "Exposed credentials will be baked into container images."
     - **WHERE:** `config/production.py : Line 5`
     - **EVIDENCE:** `DATABASE_URI = "***REDACTED_SECRET***:5432/main"`
     - **ACTIONABLE RECOMMENDATION:** "Extract into DATABASE_URL environment variable and rotate immediately."
5. **Demonstrate Live Status Triage:**
   - In the modal's triage section, click **"Dismiss"**.
   - Notice that finding `F-SEC-002` is marked `DISMISSED`.
   - The backend API (`PATCH /api/v1/findings/F-SEC-002/status`) immediately recalculates the run's deterministic risk score without requiring a full pipeline re-run!

---

### Step 7: Multi-Format Reports & Instant Export
1. Click **"Reports"** in the left navigation sidebar (`/reports`).
2. Toggle between the three export format tabs:
   - **HTML Document:** Shows the styled, standalone dark-theme report in an embedded preview.
   - **Markdown:** Shows clean GitHub-flavored markdown with summary tables and evidence blocks.
   - **JSON Contract:** Shows structured JSON ready for CI/CD pipeline consumption.
3. Click **"Export HTML"** or **"Export Markdown"** to trigger an instant download to the downloads folder.
4. **Concluding statement:**
   > "Professor, this concludes our live demonstration. DeploySafe has successfully proven that agentic reasoning, grounded RAG evidence, and deterministic risk math provide an actionable pre-deployment intelligence gate."

---

## 3. Emergency Troubleshooting Reference

| Potential Situation | Root Cause | Immediate Resolution |
| :--- | :--- | :--- |
| Frontend displays "Backend offline" | FastAPI server was stopped | Run `uvicorn backend.app.main:app --port 8000 --reload` |
| No historical runs in table | SQLite database is fresh | Click "Analyze" -> "Run Deployment Analysis" to seed a run in 2 seconds |
| API port conflict on 8000 | Another process is on port 8000 | Kill port 8000 process via `Get-Process` or run backend on `--port 8001` and update `.env` |
| Pytest warnings | Deprecation notice in starlette test client | Safe to ignore; all 62 assertions pass green |
