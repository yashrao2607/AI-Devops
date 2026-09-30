# DeploySafe — Phase 4 Live Demonstration & Viva Guide

## 1. Overview
This guide provides the exact sequence of steps to demonstrate the Phase 4 **Risk Engine + Professional Product UI** capabilities implemented in DeploySafe.

---

## 2. Key Talking Points for Evaluators
1. **Deterministic Risk Scoring:** The LLM does **NOT** generate the risk score. Specialized agents and deterministic tools detect candidate findings; the Critic Agent validates them; the Deduplication Service merges duplicates; and the `RiskEngine` calculates a mathematically grounded score bounded between 0 and 100.
2. **Formula Transparency:** Click **"How is this calculated?"** on the Dashboard or Runs page to display the exact formula:
   $$\text{Score} = \min\left(100.0, \text{round}\left(\sum \text{weight} \times \text{confidence} \times \text{impact}\right)\right)$$
3. **No Hallucinated Findings:** The Critic Agent cross-references cited file paths against physical disk files before validating.
4. **Deduplication:** When multiple agents detect overlapping issues on the same file lines, DeploySafe merges them into a single canonical finding, links merged agent attributions, and avoids double-counting score points.

---

## 3. Step-by-Step Live Demo Script

### Step 1: Launch Backend & Frontend
Ensure the FastAPI backend and Vite frontend are running:
```bash
# Terminal 1: Backend
uvicorn backend.app.main:app --port 8000 --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```
Open your browser to `http://localhost:5173/`.

---

### Step 2: Overview Dashboard (`/`)
1. Observe the **Risk Score Hero Gauge** displaying the current evaluated risk:
   - For `deploysafe-analysis-demo`, observe **Risk Score: 100 / 100 (CRITICAL RISK)**.
2. Click **"How is this calculated?"** next to the score.
   - Show the evaluator the exact mathematical formula, project-defined severity weights (Critical=35, High=25, Medium=15, Low=7), and confidence multipliers.
3. Review the **Severity Breakdown Cards** showing real counts:
   - Critical: 2
   - High: 5
   - Medium: 0
   - Low: 0
   - Critic Validated: 6
4. Inspect the **Top Validated Findings Table**:
   - Point out the **Risk Contribution** column showing exact additions (e.g. `+35 pts`, `+25 pts`).
   - Note the deduplication badge showing merged duplicate detections.

---

### Step 3: Trigger an Analysis (`/analyze`)
1. Navigate to **Analyze** in the left navigation sidebar.
2. Target the local demonstration repository:
   - Path: `demo-repos/deploysafe-analysis-demo`
   - Branch: `main`
3. Click **"Run Deployment Analysis"**.
4. Observe the **Live Agent Activity & Telemetry Timeline**:
   - Watch the 8 agents execute sequentially or in parallel:
     - `Code Analysis Agent`
     - `Dependency Agent`
     - `Configuration Agent`
     - `Test Agent`
     - `RAG / Documentation Agent`
     - `Security Analysis Agent`
     - `Critic Agent`
     - `Report Generation Agent`
   - Real durations (in seconds), tools invoked, and finding counts update live.
5. Once completed, note the **Deterministic Risk Score Banner** displaying `100 / 100 CRITICAL RISK` and `7 canonical findings (1 merged duplicates)`.

---

### Step 4: Run Details & Agent Telemetry (`/runs`)
1. Navigate to **Runs** in the left sidebar.
2. The table shows all historical runs chronologically with Run ID, Risk Score, findings counts, duration, and timestamp.
3. Click **"Inspect"** on the latest run.
4. In the detailed modal:
   - Inspect the **Active Score Contributors** list showing every single validated finding and its exact points contribution.
   - Inspect the **Excluded from Score Calculation** section showing duplicates or unverified items.
   - Inspect the **Agent Execution Telemetry** grid showing the exact runtime duration and tools called for each agent.

---

### Step 5: Findings Directory & Status Triage (`/findings`)
1. Navigate to **Findings** in the left sidebar.
2. Test the **Search Input**: Type `REDIS` or `requests` or `payment` to filter in real time.
3. Test the **Filter Toolbar**:
   - Filter by Severity: `CRITICAL`, `HIGH`.
   - Filter by Status: `VALIDATED`, `DUPLICATE`, `DISMISSED`.
4. Click **"Inspect"** on a finding (e.g. `F-SEC-001` or `F-RAG-001`).
   - In the modal, explain the 5 core questions answered:
     - **WHAT:** Analysis summary.
     - **WHY:** Why this matters & deployment impact.
     - **WHERE:** Verified file path and 1-indexed line numbers.
     - **EVIDENCE:** Line-accurate code snippet evidence with one-click copy.
     - **ACTION:** Actionable remediation recommendation.
5. Demonstrate **Status Triage**:
   - Click **"Dismiss"** on a finding.
   - Observe that the finding is marked `DISMISSED` and its score contribution immediately drops to `0 pts`, deterministically recalculating the run's risk score on the backend!

---

### Step 6: Multi-Format Reports & Exports (`/reports`)
1. Navigate to **Reports** in the left sidebar.
2. Toggle between the 3 export formats:
   - **HTML Document:** Standalone styled dark-mode report displayed in an interactive container.
   - **Markdown:** Clean documentation-ready Markdown with markdown tables.
   - **JSON Contract:** Structured API contract ready for CI/CD gates.
3. Click **"Export HTML"** or **"Export Markdown"** to download the report directly to disk.

---

## 4. Test Verification Commands
Run the automated pytest test suite to verify full backend, risk engine, and deduplication correctness:
```bash
python -m pytest backend/tests -v
```
All 62 tests pass with 0 failures.
