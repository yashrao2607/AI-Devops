# DeploySafe Deterministic Risk Model

## Executive Overview
DeploySafe utilizes a strictly **deterministic, audit-grounded mathematical risk scoring engine** (`RiskEngine`). The system does **NOT** delegate the final numerical risk score calculation to an LLM.

Instead, LLM agents (specialized by domain) produce candidate findings with concrete repository evidence. Those findings are then validated by the Critic Agent, clustered and deduplicated by the Deduplication Service, and passed into the deterministic Risk Engine.

---

## 1. Severity Weights
The baseline contribution of a finding is governed by project-defined severity weights:

| Severity | Base Weight (Points) | Product Rationale |
| :--- | :--- | :--- |
| **CRITICAL** | **35 pts** | Direct blockers (e.g. hardcoded production database credentials, critical CVEs). |
| **HIGH** | **25 pts** | Significant drifts (e.g. unpinned dependencies/containers, documented required services missing). |
| **MEDIUM** | **15 pts** | Warning-level risks (e.g. missing test coverage on critical payment logic). |
| **LOW** | **7 pts** | Hygiene and cosmetic issues (e.g. minor documentation omissions). |

*Note: These weights are DeploySafe's internal scoring design and do not represent an official external regulatory standard.*

---

## 2. Confidence & Impact Multipliers
To account for evidence certainty and blast radius, each finding's points are adjusted by two deterministic multipliers:

### Confidence Multiplier ($M_{\text{conf}}$)
- **HIGH:** `1.0` (Grounded in explicit static AST or direct tool scan)
- **MEDIUM:** `0.8` (Correlated across multiple files or partial match)
- **LOW:** `0.6` (Heuristic or inferred finding)

### Impact / Scope Multiplier ($M_{\text{impact}}$)
- **CRITICAL / HIGH:** `1.0` (Affects production traffic or deployment integrity)
- **MEDIUM:** `0.8` (Affects staging or partial subsystem)
- **LOW:** `0.6` (Localized internal helper or non-blocking)

---

## 3. Mathematical Formula
For each candidate finding $f \in \mathcal{F}$:
$$\text{points}(f) = \begin{cases} \text{weight}(f) \times M_{\text{conf}}(f) \times M_{\text{impact}}(f) & \text{if } f \text{ is } \textbf{VALIDATED} \\ 0 & \text{otherwise} \end{cases}$$

The raw score is computed as:
$$\text{Raw Score} = \sum_{f \in \mathcal{F}_{\text{canonical}}} \text{points}(f)$$

The final normalized risk score is capped between $0$ and $100$:
$$\text{Risk Score} = \min\left(100.0, \text{round}\left(\text{Raw Score}\right)\right)$$

---

## 4. Risk Tiers & Interpretation
The continuous score maps directly to four discrete risk levels:

| Score Range | Risk Level | Interpretation | Action Required |
| :--- | :--- | :--- | :--- |
| **0 – 24** | **LOW** | Clean or negligible deployment drift. | Ready for automated deployment. |
| **25 – 49** | **MODERATE** | Minor warnings or single medium risk. | Review recommended before production push. |
| **50 – 74** | **HIGH** | Severe unpinned configs or multiple vulnerabilities. | Manual sign-off required. |
| **75 – 100** | **CRITICAL** | Deployment blocker (e.g. exposed secrets). | Deployment strictly aborted. |

---

## 5. Exclusions & Audit Policy
Findings with the following statuses contribute **$0.0$ points** and are itemized in `excluded_findings`:
1. **DUPLICATE:** Redundant detection merged into a canonical finding.
2. **REJECTED / INSUFFICIENT_EVIDENCE:** Dismissed by Critic Agent due to lack of ground truth or file non-existence.
3. **NEEDS_REVIEW:** Unverified candidate findings pending developer confirmation.
4. **DISMISSED:** Manually triaged false positives overridden by developers.

---

## 6. Reproducibility & Determinism
Given an identical set of findings, the Risk Engine guarantees:
- Exact same numerical score ($\Delta = 0.0$).
- Exact same itemized contributor points.
- Zero non-deterministic drift across platform environments.
