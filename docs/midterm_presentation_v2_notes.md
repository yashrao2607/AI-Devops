# DeploySafe — Midterm Presentation Speaker Notes (Refined 10-Slide Edition)

> **Course:** CSE 4011 — Intelligent Developer Tools and AI DevOps Workflows  
> **Faculty Mentors:** Dr. Kiran Khatter & Mr. Naveen Singh  
> **Evaluation Component:** A2 – Project Phase Evaluation 2 (Mid-Term Examination · 30% Weightage · 5–9 Oct 2026)  
> **Format:** 10 Slides (16:9 Widescreen, Clean Technical Light Theme)  
> **Generated Decks:** `DeploySafe_Midterm_Presentation_CSE4011.pptx` & `DeploySafe_Midterm_Presentation_v3.pptx`  
> **Student:** Yash Rao (Batch 2023–27, 7th Semester)

---

## Slide 1: Title & Course Context

### Slide Purpose
Sets a professional, grounded tone and establishes direct alignment with CSE 4011 and faculty evaluators Dr. Kiran Khatter & Mr. Naveen Singh.

### Talking Points
- "Good morning Dr. Kiran Khatter and Mr. Naveen Singh. Today I am presenting **DeploySafe**, an automated pre-deployment risk analysis tool for DevOps pipelines."
- "This submission is for **Project Phase Evaluation 2 (A2)**, weighted at **30%** in CSE 4011."
- "DeploySafe inspects software repositories before deployment to detect configuration drift, unpinned dependencies, and missing environment secrets that standard CI tests miss."
- "Findings are validated against actual files on disk by a Critic agent, and scored using a deterministic mathematical formula."

### Likely Professor Question
**Q (Mr. Naveen Singh):** *"Why is this problem best solved by an AI DevOps tool rather than standard static analysis tools like SonarQube or ESLint?"*

### Concise Answer
**A:** "Static analysis tools operate on isolated files checking predefined syntactic patterns and AST rules. They cannot understand natural language requirements written in documentation or cross-correlate them with deployment manifests. DeploySafe uses specialized AI domain agents and semantic RAG to correlate intent with configuration—for example, discovering that a Redis cache specified in `README.md` is omitted from `docker-compose.yml`."

---

## Slide 2: Why Green Builds Still Fail in Production

### Slide Purpose
Clearly articulates the real-world software engineering problem with concrete code examples, and explains where DeploySafe fits in the CI/CD pipeline.

### Talking Points
- "Every engineering team has seen unit tests pass in CI only for the application to crash on container startup in production."
- "CI tests check code logic in isolation, but they do not check deployment environment parity:
  1. **Missing Services in Compose:** Source code calls `redis://redis:6379`, but Redis is missing from `docker-compose.yml`. Tests pass, but the container crashes on boot.
  2. **Unpinned Dependency Drift:** Packages in `requirements.txt` lack pinned versions; a new minor release upstream breaks production while local CI runners succeed on cache.
  3. **Undeclared Variables:** Code calls `os.environ['DATABASE_URL']` without fallback, and the variable is omitted from `.env.example`, causing runtime crashes."
- "DeploySafe acts as an automated pre-flight gatekeeper right after unit tests pass, checking the full repository context before code reaches the production cluster."

### Likely Professor Question
**Q (Dr. Kiran Khatter):** *"Don't staging environments catch these configuration problems before production?"*

### Concise Answer
**A:** "Staging environments only catch scenarios covered by existing integration tests against running infrastructure. They miss unpinned container tags that change overnight and missing documentation requirements before release. DeploySafe catches these statically in under 5 seconds before infrastructure is provisioned."

---

## Slide 3: Course Alignment & Evaluation Rubrics (A2 · 30%)

### Slide Purpose
Directly maps project deliverables to the 4 components of the A2 Midterm Rubric from the CSE 4011 Course Handout.

### Talking Points
- "This slide demonstrates our direct mapping to the A2 Mid-Term Evaluation Rubrics (30% weightage):
  - **1. RAG & Code Retrieval (10%):** ChromaDB persistent vector database with markdown chunking that preserves line numbers. Indexes documentation to extract required services and ports.
  - **2. CI/CD & Release Automation (10%):** Pre-deployment verification gate that emits non-zero exit codes on Critical risk to block broken merges.
  - **3. Test Suite & AST Inspection (5%):** Python `ast` parser for code verification + 62 unit and integration tests running in CI.
  - **4. Working Prototype & Docs (5%):** Functional FastAPI backend, React 19 web interface, Docker Compose orchestration, and Swagger OpenAPI docs."

### Likely Professor Question
**Q (Dr. Kiran Khatter):** *"How does DeploySafe satisfy Course Outcomes CO1, CO2, and CO3?"*

### Concise Answer
**A:** "DeploySafe fulfills CO1 through prompt engineering and model selection; CO2 through semantic code search with ChromaDB and automated test analysis; and CO3 through an end-to-end AI-augmented release gate."

---

## Slide 4: System Architecture & Agent Responsibilities

### Slide Purpose
Explains the 5-stage data flow and justifies why specialized domain agents are used instead of a single monolithic prompt.

### Talking Points
- "Here is our 5-stage pipeline:
  1. **Ingestion & AST:** Recursively parses repository file trees, Python ASTs, and dependencies.
  2. **ChromaDB RAG:** Chunks and indexes architectural intent into a local vector store.
  3. **Specialist Agents:** The Orchestrator dispatches agents concurrently in a thread pool:
     - *Code Agent:* AST error handling, bare excepts, missing timeouts.
     - *Config Agent:* Dockerfiles and docker-compose service definitions.
     - *Dependency Agent:* Version pinning and missing native compilation flags.
     - *Doc RAG Agent:* ChromaDB queries for required services and ports.
  4. **Critic Validation:** Physical line verification on disk.
  5. **Risk Formula:** Deterministic 0–100 mathematical risk calculation."
- "Dividing work across specialist agents avoids prompt attention loss, runs concurrently in ~1.8 seconds, and isolates findings for validation."

### Likely Professor Question
**Q (Mr. Naveen Singh):** *"How are the agents orchestrated?"*

### Concise Answer
**A:** "The Orchestrator inspects the repository's technology stack (e.g., Python, Docker, Node) and dispatches independent domain agents concurrently using a thread pool before aggregating findings into a Pydantic blackboard."

---

## Slide 5: RAG in Practice: Detecting Configuration Drift

### Slide Purpose
Provides a concrete case study showing ChromaDB retrieval in action, linking documentation context to deployment manifests.

### Talking Points
- "This slide demonstrates our RAG engine in action, fulfilling the 10% RAG requirement."
- "Our ingestion pipeline parses `README.md`, splits text into section-aware chunks with line numbers, and stores dense embeddings in ChromaDB."
- "Case study on our `demo-microservice` evaluation repo:
  - **Retrieved Intent (`README.md`, line 21):** *'Requires Redis for session caching: REDIS_URL=redis://redis:6379/0'*
  - **Inspected Manifest (`docker-compose.yml`, lines 1–12):** Only the `web` service is defined; Redis is missing.
  - **Critic Verification:** Checked disk file and confirmed Redis is absent.
  - **Result:** Flagged as High Severity risk: Web service will fail health checks on container startup."

### Likely Professor Question
**Q (Mr. Naveen Singh):** *"What happens if a repository has no documentation?"*

### Concise Answer
**A:** "DeploySafe handles missing documentation gracefully. If no markdown files exist, the RAG agent returns an empty context set, and the other agents continue static code, manifest, and dependency analysis without interruption."

---

## Slide 6: Deterministic Risk Scoring vs. LLM Hallucinations

### Slide Purpose
Explains how DeploySafe eliminates subjective or hallucinated risk numbers by separating LLM reasoning from mathematical scoring.

### Talking Points
- "The biggest issue with AI developer tools is hallucinated metrics. If an LLM directly outputs a risk score like '85', that number is subjective and cannot be trusted in production."
- "DeploySafe uses a 3-stage validation pipeline:
  1. **Stage 1 (LLM Proposal):** Agent proposes candidate finding with severity and confidence.
  2. **Stage 2 (Critic Verification):** Critic checks target file lines and heuristic flags on disk.
  3. **Stage 3 (Deterministic Formula):** Pure Python arithmetic computes the score:
     $$Score = \min\left(100,\; \sum (\text{BaseWeight} \times \text{Confidence})\right)$$
     - Critical = 40 pts, High = 25 pts, Medium = 12 pts, Low = 5 pts.
     - Threshold: Score $\ge 70 \implies$ **NO-GO** (Exit Code 1); Score $< 70 \implies$ **GO**."
- "The LLM never generates numbers or scores directly. The calculation is 100% deterministic."

### Likely Professor Question
**Q (Dr. Kiran Khatter):** *"Can an agent fabricate a finding for a file that doesn't exist?"*

### Concise Answer
**A:** "No. The Critic agent opens the target file on disk, validates line boundary bounds, and checks false-positive heuristics. If the file or lines do not exist, the finding is immediately rejected and excluded from risk scoring."

---

## Slide 7: The Working Product: Web Dashboard

### Slide Purpose
Showcases the operational React 19 web console with real screenshots of the dashboard, findings directory, and execution telemetry.

### Talking Points
- "Here is the running DeploySafe web console built in React 19, TypeScript, and Tailwind CSS."
- "The **Risk Overview Dashboard** features a 0–100 risk score hero card, severity breakdowns, and a real-time Critic validation health indicator."
- "The **Findings Directory** provides line-accurate code citations, confidence factors, and copyable CLI remediation commands."
- "The **Execution Telemetry** view displays per-agent execution times (~1.8s per agent) and status polling."

### Likely Professor Question
**Q (Mr. Naveen Singh):** *"How does the frontend communicate with the backend?"*

### Concise Answer
**A:** "The React frontend communicates with our FastAPI REST gateway via typed API endpoints (`/api/v1/analyze`, `/api/v1/repositories`, `/api/v1/health`), using Axios with client-side polling and reactive state management."

---

## Slide 8: Implementation Status & Test Verification

### Slide Purpose
Provides an honest, realistic breakdown of what is currently operational vs. what is scheduled for the final term, backed by 62 automated tests.

### Talking Points
- "This slide gives an honest view of our progress at midterm:
  - **Currently Implemented & Tested:**
    - Repository ingestion and Python AST parser
    - ChromaDB vector store and markdown chunker
    - 4 specialist agents (Code, Config, Dependency, Doc RAG)
    - Critic disk line verification engine
    - Deterministic risk formula and Go/No-Go release gate
    - FastAPI REST service and React 19 web console
  - **In Progress / Next Phase:**
    - GitHub Actions PR bot integration
    - Automated patch generation for simple configuration fixes."
- "Our automated test suite contains **62 passing tests** in pytest covering AST parsing, vector search, agent prompts, Critic line checks, and risk calculation with zero external API dependencies."

### Likely Professor Question
**Q (Dr. Kiran Khatter):** *"How do you ensure your automated tests are reliable?"*

### Concise Answer
**A:** "Our test suite exercises real file tree traversals, real ChromaDB vector insertions and cosine queries, real AST code parsing, and real mathematical risk calculations with zero mocking of internal business logic."

---

## Slide 9: Docker Architecture & Tested Repositories

### Slide Purpose
Demonstrates containerization engineering rigor and shares benchmark metrics across real open-source repositories.

### Talking Points
- "DeploySafe is containerized via Docker Compose:
  1. **FastAPI Backend:** Runs `python:3.11-slim` under a dedicated non-root user `appuser` (UID 1000) with a volume mount for ChromaDB persistence.
  2. **Frontend & Reverse Proxy:** Lightweight 21MB `nginx:1.27-alpine` multi-stage build that proxies `/api/` calls, eliminating CORS issues.
  3. **Bridge Network:** Internal `deploysafe-net` bridge network with Docker health checks."
- "Tested across real open-source repositories:
  - `web-scrape` (Node.js): Detected unpinned dependencies and missing production build script.
  - `bottle-app` (Python WSGI): Detected missing production WSGI server in Dockerfile.
  - `demo-microservice` (Python): Detected missing Redis service and undeclared `DATABASE_URL`.
  - **Execution speed:** Approximately 5.0 seconds end-to-end on Groq Llama-3."

### Likely Professor Question
**Q (Mr. Naveen Singh):** *"Why use a multi-stage Docker build for the frontend rather than running Node.js in production?"*

### Concise Answer
**A:** "A multi-stage build compiles our React application into lightweight static files during the build phase and discards all Node.js build tooling, producing an ultra-secure 21MB Alpine Nginx container with zero unnecessary runtime dependencies."

---

## Slide 10: Project Roadmap & Individual Responsibilities

### Slide Purpose
Outlines practical next milestones for the final evaluation (A3) and details individual contributions under Criterion C10.

### Talking Points
- "To conclude, DeploySafe provides automated pre-deployment risk analysis to catch configuration drift before production."
- "**Roadmap for Final Evaluation (A3):**
  - *GitHub Action Bot:* Run analysis on pull request events and post summary comments.
  - *Diff-Targeted Scans:* Inspect only changed files to reduce analysis execution time to under 2.0 seconds.
  - *Auto-Fix PRs:* Generate ready-to-merge patches for missing environment variables or unpinned tags."
- "**Individual Responsibilities (Yash Rao):**
  - Backend & API: Designed FastAPI endpoints and Pydantic schemas.
  - RAG & Agents: Implemented ChromaDB indexing, agent prompts, and Critic verification.
  - Risk Formula: Developed the deterministic risk scoring and threshold logic.
  - DevOps & Testing: Created Docker Compose setup, Nginx proxy, 62 unit tests, and React dashboard."
- "Thank you Dr. Kiran Khatter and Mr. Naveen Singh. I am ready for the live demonstration and your questions."

### Likely Professor Question
**Q (Both Faculty):** *"What was the single most challenging architectural hurdle you solved in this midterm?"*

### Concise Answer
**A:** "Eliminating hallucination in risk scoring. By strictly restricting the LLM to evidence-backed finding proposals and delegating verification to the Critic and scoring to pure Python arithmetic, we created a system that engineers and managers can mathematically trust."
