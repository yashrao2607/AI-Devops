# DeploySafe V2 — Demonstration Script & Walkthrough

## 1. Demo Objectives
Demonstrate the new empirical features implemented in Phase 7 / V2:
1. Custom repository configuration (`deploysafe.yml`)
2. Deterministic Change Impact Blast Radius
3. Historical risk trends and recurring finding detection
4. Safe unified diff patch preview with human approval banner

---

## 2. Step-by-Step Demonstration Flow

### Step 1: Start the Platform
```powershell
# In terminal 1 (Backend):
cd d:\NAVEEN-SIR_PROJECT
$env:PYTHONPATH="."
uvicorn backend.app.main:app --reload --port 8000

# In terminal 2 (Frontend):
cd d:\NAVEEN-SIR_PROJECT\frontend
npm run dev
```
Navigate browser to: `http://localhost:5173`

---

### Step 2: Custom Repository Configuration
1. Inspect `demo-repos/evaluation/case_01_config_risk/deploysafe.yml` (or sample):
   ```yaml
   version: "1"
   fail_threshold: 65
   critical_findings_limit: 0
   high_findings_limit: 2
   exclude_paths:
     - "tests/**"
   ```
2. Trigger deployment risk analysis on this repository.
3. Observe how the gate policy adheres to the custom repository thresholds rather than hardcoded global defaults.

---

### Step 3: Change Impact Blast Radius
1. Open the **Runs** view in the UI (`/runs`).
2. Select any completed run and click the **Run Details** modal.
3. Switch from the **Summary** tab to the **Change Impact (V2)** tab.
4. Point out:
   - **Blast Radius Badge**: Highlights `CRITICAL`, `HIGH`, `MEDIUM`, or `LOW`.
   - **Affected Components Table**: Lists structural components (e.g., `Data / Migrations`, `Security / Auth`, `Infrastructure / Containers`).
   - **Mandatory Verification Checks**: Displays required pre-deployment safety steps (e.g., *"Run database migration dry-run and verify rollback script"*).

---

### Step 4: Proposed Remediation Patch Preview
1. Navigate to the **Findings** view (`/findings`).
2. Click on any finding with code remediation guidance.
3. Click the **"Preview Proposed Patch"** button.
4. Point out:
   - The amber **Human-in-the-Loop Review Banner**: *"CAUTION: AI-generated remediation patches must be reviewed and tested by a human engineer before applying."*
   - Syntax-colored standard unified diff displaying additions (`+`) in emerald green and removals (`-`) in rose red.
   - Clarify that DeploySafe deliberately **does not auto-commit** code without human engineering approval.

---

### Step 5: Historical Analytics
1. Navigate to the **Repositories** view (`/repositories`).
2. View repository history metrics:
   - Historical risk score trends.
   - Recurring findings flagged across consecutive runs.
   - Gate pass/fail ratio and block velocity.

---

## 3. Key Talking Points for Evaluators
- **Safety First**: Autonomous AI agent writes are dangerous; DeploySafe V2 empowers human reviewers with actionable unified diffs.
- **Deterministic Blast Radius**: Fast (<10ms) rule-based impact mapping ensures deployment teams know exactly what verification checks are mandatory before hitting deploy.
- **Enterprise Ready**: Version-controlled `deploysafe.yml` allows repository owners to self-govern risk policies.
