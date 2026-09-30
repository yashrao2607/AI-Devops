# DeploySafe — Midterm Presentation Speaker Notes & Viva Defense Guide

> **Course:** Agentic AI (CSE3101)  
> **Topic:** DeploySafe Midterm Presentation  
> **Format:** 15 Slides (16:9 Widescreen)  
> **Source Deck:** `DeploySafe_Midterm_Presentation.pptx`

---

## Slide 1: Title & Overview

### 30–60 Second Presenter Script
"Good morning Professor and fellow engineers. Today we present **DeploySafe**, an autonomous multi-agent platform designed to evaluate software deployment readiness before code reaches production environments. In modern engineering teams, CI/CD pipelines automate the mechanics of compilation, linting, and testing. However, passing unit tests does not guarantee that a change is safe to release. DeploySafe introduces an intelligent reasoning layer that evaluates heterogeneous signals—source code, manifests, Docker files, test coverage, and documentation—grounding every finding in concrete evidence and computing a deterministic, mathematical deployment risk score."

### Anticipated Professor Question
**Q:** *Why is this problem best solved by Agentic AI rather than standard static analysis or SonarQube?*

### Concise Answer
**A:** "Standard static analysis tools operate in isolated AST silos on individual files. They cannot correlate human architectural intent in natural language documentation against deployment manifests—such as discovering that a documented required service like Redis is completely omitted from `docker-compose.yml`. DeploySafe uses specialized agents that reason across diverse domains, query vector RAG for documentation intent, use typed tools, and submit candidate findings to an adversarial Critic agent for physical disk verification."

---

## Slide 2: The Deployment Problem

### 30–60 Second Presenter Script
"Every software engineer has experienced a deployment incident where code passed all CI checks green, but immediately failed upon deployment. The traditional development lifecycle runs tests, builds images, and pushes containers. But why do outages still happen? Because deployment risk is multi-dimensional. A change may compile cleanly while introducing silent supply-chain drift through unpinned packages, hardcoded localhost URLs that fail inside containers, or undocumented environment dependencies. Traditional tools execute in disjointed silos without evaluating the systemic deployment context."

### Anticipated Professor Question
**Q:** *Wouldn't comprehensive end-to-end staging tests catch these issues?*

### Concise Answer
**A:** "Staging environments only test scenarios developers explicitly planned and scripted. They fail to catch unpinned upstream container tags that change overnight, hidden credential leaks checked into repo files, or drift between documented architecture and actual compose files before deployment occurs."

---

## Slide 3: CI/CD Executes. DeploySafe Analyzes.

### 30–60 Second Presenter Script
"To be strictly clear about our product positioning: DeploySafe does not replace CI/CD pipelines. CI/CD is an execution engine—it runs commands, builds containers, and reports binary exit codes (0 or 1). DeploySafe is an analytical intelligence layer. It inspects repository context, understands deployment intent, correlates cross-file signals, and explains risks with line-accurate evidence. CI/CD asks 'did this command run?'; DeploySafe asks 'is this change safe to deploy to production?'"

### Anticipated Professor Question
**Q:** *How do you prevent DeploySafe from becoming a slow bottleneck in fast CI/CD loops?*

### Concise Answer
**A:** "By employing specialized parallel agents and targeted RAG retrieval. The Orchestrator plans execution based on discovered tech stacks and runs independent domain agents concurrently in a Python thread pool. In our verified test runs, full multi-agent analysis, Critic validation, and risk scoring complete in under 2.5 seconds."

---

## Slide 4: Meet DeploySafe — Architecture Overview

### 30–60 Second Presenter Script
"DeploySafe takes five core repository signals: source code, dependencies, configuration files, test suites, and documentation. These feed into the DeploySafe multi-agent engine, where six specialized agents, a Chroma vector RAG store, an adversarial Critic, a deduplication service, and a deterministic Risk Engine process candidate issues. The output is auditable: a bounded 0–100 risk score, validated findings with exact line numbers, explanations answering What, Why, and Where, and actionable fixes."

### Anticipated Professor Question
**Q:** *Why is repository documentation treated as an active signal?*

### Concise Answer
**A:** "Documentation represents human architectural contracts. When developers document in `README.md` that an environment variable is mandatory for distributed sessions, that contract must be honored in deployment configurations. DeploySafe's Documentation RAG agent extracts these requirements and cross-examines runtime manifests to detect silent configuration drift."

---

## Slide 5: From Repository to Risk Insight (Processing Pipeline)

### 30–60 Second Presenter Script
"Here is the exact 7-step pipeline implemented in our codebase. First, the repository is loaded and secrets are redacted. Second, files and manifests are categorized. Third, documentation is chunked and embedded into our local Chroma vector database. Fourth, six specialized CrewAI agents execute in parallel. Fifth, candidate findings enter our Critic agent, which checks physical disk paths to prevent hallucinations. Sixth, the deduplication service clusters overlapping line ranges. Finally, the deterministic Risk Engine computes points without LLM numerical hallucination."

### Anticipated Professor Question
**Q:** *What happens if an LLM agent hallucinates a file that does not exist?*

### Concise Answer
**A:** "The Critic Agent performs a physical filesystem check against the repository snapshot. If the cited `file_path` is missing or the evidence snippet is empty, the finding is assigned status `REJECTED`, labeled as a hallucination, and given exactly 0 points in the risk score."

---

## Slide 6: DeploySafe Technical Architecture

### 30–60 Second Presenter Script
"This slide maps our technical architecture. At the top is our React 18, TypeScript, and TailwindCSS interface. It communicates via versioned REST APIs with our FastAPI gateway. The gateway dispatches the `DeploySafeAnalysisFlow`, which manages agent lifecycles, vector RAG retrieval, and deterministic tool execution. Crucially, notice the bottom layer: candidate findings flow through the Critic, the Deduplication service, and finally the deterministic Risk Engine before results are stored in SQLite and emitted to the UI."

### Anticipated Professor Question
**Q:** *How is CrewAI integrated into this architecture?*

### Concise Answer
**A:** "We utilize CrewAI's state flow abstraction in `DeploySafeAnalysisFlow`. The flow manages repository context building, dynamic task planning based on detected technologies, parallel execution of domain agents using a thread pool, and state persistence for auditing."

---

## Slide 7: Why Multi-Agent? Specialized Domain Delegation

### 30–60 Second Presenter Script
"Why did we implement 8 specialized agents rather than asking one large language model prompt to analyze everything? In production repositories, monolithic prompts suffer from severe attention dilution and tool-selection failures. By dedicating specialized agents—Code, Dependency, Config, Test, RAG, and Security—each agent has an isolated system prompt, restricted tool contracts, and domain-specific rules. The Critic agent serves as an independent gatekeeper, and the Report agent formats structured outputs."

### Anticipated Professor Question
**Q:** *Do all 8 agents run on every repository?*

### Concise Answer
**A:** "No. The Orchestrator evaluates the repository structure during Step 2. If a repository has no Dockerfile, the Configuration agent is skipped. If there are no dependency manifests, the Dependency agent is skipped. This dynamic planning optimizes runtime duration and token usage."

---

## Slide 8: How DeploySafe Understands the Repository (RAG)

### 30–60 Second Presenter Script
"Slide 8 demonstrates our RAG foundation built in Phase 2 and leveraged in Phase 3. Documentation is discovered, chunked along headings and code boundaries, and indexed into a local Chroma vector database using 384-dimensional embeddings. On the right is a real query executed on our demo repository: the RAG agent queried for deployment requirements, retrieved lines 5–9 of `README.md` requiring `REDIS_URL`, and cross-examined `docker-compose.yml` to discover that `REDIS_URL` was omitted. This produced validated finding `F-RAG-001` contributing +25 points to the risk score."

### Anticipated Professor Question
**Q:** *Why use local embeddings instead of OpenAI or Gemini embeddings?*

### Concise Answer
**A:** "We architected an embedding factory that supports Gemini, Groq, and a local offline embedding provider. The local provider ensures 100% deterministic vector generation, zero external network latency, zero API costs, and allows our 62-test automated suite to run offline in under 7 seconds."

---

## Slide 9: Agents Don't Just Guess: Typed Tool Contracts

### 30–60 Second Presenter Script
"In DeploySafe, agents cannot make vague assertions. Every finding must be grounded in observable facts via typed tool contracts. We built repository file slicers, git diff parsers, dependency manifest AST analyzers, a security scanner with automated secret masking, and a sandboxed safe command executor. On the right is an actual finding from our demo run: `F-SEC-002`. Notice that the hardcoded database credential in `config/production.py` has been automatically sanitized as `***REDACTED_SECRET***`, ensuring credentials never leak into LLM prompts or stored reports."

### Anticipated Professor Question
**Q:** *How does the sandboxed safe executor protect against command injection?*

### Concise Answer
**A:** "The safe command executor strictly validates binary paths against a hardcoded allowlist (e.g. `pytest`, `git`), disallows shell meta-characters, executes commands without shell interpolation (`shell=False`), and enforces a strict timeout."

---

## Slide 10: From Findings to Deterministic Risk

### 30–60 Second Presenter Script
"One of DeploySafe's core architectural tenets is that the LLM does not calculate the final numerical risk score. If an LLM is asked to output a score from 1 to 100, its response is non-deterministic and irreproducible. Instead, our `RiskEngine` calculates scores using pure arithmetic: $\text{Score} = \min(100.0, \text{round}(\sum \text{weight} \times \text{confidence} \times \text{impact}))$. Severity weights are project-defined: Critical=35, High=25, Medium=15, Low=7. Duplicate and rejected findings contribute 0 points. In our demo repository, 2 Critical and 4 Validated High findings yielded a raw score of 170, which is capped at 100.0 CRITICAL RISK."

### Anticipated Professor Question
**Q:** *Are these severity weights based on an industry standard like CVSS?*

### Concise Answer
**A:** "No, and we are explicitly transparent about this. These weights are DeploySafe project-defined scoring rules designed for deployment readiness triage. They are not an external regulatory standard, nor do they guarantee absolute deployment safety."

---

## Slide 11: DeploySafe Product UI Experience

### 30–60 Second Presenter Script
"Slide 11 showcases authentic, unedited screenshots of our running product UI. On the top left is our Overview Dashboard featuring the 100/100 CRITICAL risk hero gauge, severity breakdown cards, and the 'How is this calculated?' formula modal. Top right is our Findings Directory displaying live score contributions like +35 pts and multi-attribute filters. Bottom left shows our Run History timeline with agent execution telemetry. Bottom right shows our multi-format report viewer supporting HTML previews, Markdown, and JSON exports."

### Anticipated Professor Question
**Q:** *How are the frontend loading and error states handled?*

### Concise Answer
**A:** "Every screen implements real loading spinners and contextual empty states. When a run has 0 findings, the system explicitly displays '0 deployment findings detected' rather than asserting 'guaranteed safe', maintaining honest technical reporting."

---

## Slide 12: Live Demonstration Flow

### 30–60 Second Presenter Script
"During our live demonstration, we will guide the evaluator through seven reproducible steps. First, we select our seeded demo repository in the UI. Second, we trigger the multi-agent analysis flow. Third, we observe real-time agent execution telemetry. Fourth, we review the vector RAG correlation between documentation and compose files. Fifth, we examine how the Critic and Deduplication services filter candidate findings. Sixth, we inspect the deterministic risk score and formula modal. Seventh, we demonstrate live triage by marking a finding as dismissed and observing the score recalculate."

### Anticipated Professor Question
**Q:** *Can this be run against an arbitrary GitHub repository right now?*

### Concise Answer
**A:** "Yes. The repository loader supports local directory paths and public GitHub repository URLs via git clone. The system clones the target, discovers files, indexes documentation into Chroma, and dispatches the agents."

---

## Slide 13: Current Implementation — Phases 1 to 4 Complete

### 30–60 Second Presenter Script
"This slide details our verified engineering progress. In Phase 1, we built the FastAPI gateway, React shell, and LLM provider factory. In Phase 2, we built repository ingestion, AST discovery, and the Chroma vector RAG store. In Phase 3, we implemented the 8 CrewAI agents, typed tools, and Critic gatekeeper. In Phase 4, we built the deterministic Risk Engine, deduplication service, and full product UI. Our automated test suite includes 62 pytest tests passing with 0 failures, and the Vite frontend compiles with 0 errors in 2.38 seconds."

### Anticipated Professor Question
**Q:** *How do you verify that your test suite is reliable and not flaky?*

### Concise Answer
**A:** "By isolating tests from external network dependencies. Our test suite uses local mock providers and offline deterministic embeddings, ensuring consistent execution in under 7 seconds with 100% reproducible results."

---

## Slide 14: What Comes Next — Phases 5 & 6

### 30–60 Second Presenter Script
"We are strictly disciplined about our phase boundaries. What we demonstrated today represents completed Phases 1 through 4. For Phase 5, scheduled for the final evaluation, we will build the GitHub Actions CI workflow, the automated PR comment bot, benchmark evaluation datasets, and adversarial prompt hardening. For Phase 6, we plan OpenTelemetry tracing, multi-tenant authentication, and production Docker distribution."

### Anticipated Professor Question
**Q:** *How will Phase 5 evaluate the accuracy of DeploySafe quantitatively?*

### Concise Answer
**A:** "In Phase 5, we will curate a benchmark evaluation dataset of 20+ open-source repositories containing known deployment bugs (e.g. CVEs, config drift, unpinned dependencies) to measure precision, recall, and false-positive rates quantitatively."

---

## Slide 15: Conclusion & Questions

### 30–60 Second Presenter Script
"In conclusion, DeploySafe bridges the gap between traditional CI compilation and deployment confidence. By combining specialized CrewAI agents, Chroma vector RAG, anti-hallucination Critic validation, and a deterministic mathematical Risk Engine, DeploySafe provides software teams with transparent, evidence-backed deployment intelligence. Thank you, and we welcome your questions and the live demonstration."

### Anticipated Professor Question
**Q:** *What was the most challenging technical hurdle in developing DeploySafe so far?*

### Concise Answer
**A:** "The most challenging hurdle was preventing LLM hallucinations and duplicate findings across overlapping agents. For instance, both the Code Agent and Security Agent frequently flag the same configuration issue. Implementing the adversarial Critic Agent and multi-attribute Deduplication Service resolved this by verifying physical disk existence and merging agent attributions without inflating the risk score."
