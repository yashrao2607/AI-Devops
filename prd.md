DEPLOSAFE — PRODUCT REQUIREMENTS DOCUMENT
0. Product decision first
Recommended stack
Layer	Primary choice	Why
Agent orchestration	CrewAI OSS	Open-source, MIT, multi-agent + Flows
Main LLM	Gemini 3.8 Flash	Current Gemini Flash model aimed at software engineering/autonomous agents; free tier currently available
Backup LLM	Groq + gpt-oss-120b	Fast; current free-plan limits are useful for a student demo
Embeddings	Gemini Embedding 2	Current, free text-input tier
Vector DB	Chroma	Open-source, Apache 2.0
Backend	FastAPI	Lightweight Python API
Frontend	React + TypeScript + Tailwind + shadcn/ui	Better polished UI than a quick prototype UI
Database	SQLite initially	Zero setup; easy for college project
Repo integration	GitHub API	Direct GitHub analysis
CI/CD integration	GitHub Actions	Automatic analysis on push/PR
Observability	OpenTelemetry + internal run logs	Free and demonstrates tracing
Deployment	Docker	Reproducible
IDE/build environment	Google Antigravity	Agentic editor with terminal/browser/agent/artifact capabilities

CrewAI is currently open source under MIT and provides Crews plus Flows; its current documentation describes Flows as the structured backbone for application state/execution.

Google currently lists Gemini 3.8 Flash as a model for long-horizon software engineering, autonomous agents and complex workflows, with free input/output pricing on the free tier. Gemini Embedding 2 currently has free text-input pricing as well.

Groq’s current rate-limit page lists, for example, openai/gpt-oss-120b at 30 RPM, 1,000 RPD, 8K TPM and 200K TPD on the free plan; limits can change, so your app should handle 429s and fallback.

Chroma is currently open source under Apache 2.0.

Antigravity is an agentic development environment with editor, terminal and browser capabilities, parallel agents, and artifacts such as plans, diffs, diagrams and recordings—so it fits the build workflow you are asking for.

1. Product Overview
1.1 Product name

DeploySafe

Tagline

Know the deployment risk before you deploy.

1.2 One-line definition

DeploySafe is a multi-agent AI deployment-readiness platform that analyzes a software repository and code changes, combines deterministic checks with LLM reasoning and repository RAG, and produces an explainable deployment-risk report.

1.3 Problem

Before deploying software, developers may need to inspect:

code changes
dependencies
configuration
secrets
tests
Docker/deployment files
documentation
CI configuration

Manual review is time-consuming and can miss interactions between these areas.

Existing CI/CD pipelines primarily execute predefined checks.

DeploySafe adds an AI analysis and reasoning layer:

What changed? What risks does it introduce? What evidence supports that risk? What should the developer fix?

2. Product Vision

DeploySafe should become a pre-deployment intelligence layer sitting beside CI/CD.

Target flow
Developer
   ↓
GitHub Pull Request
   ↓
GitHub Actions
   ↓
DeploySafe
   ↓
Repository ingestion
   ↓
Deterministic checks
   ↓
Multi-agent analysis
   ↓
RAG
   ↓
Critic / validation
   ↓
Risk scoring
   ↓
Deployment-readiness report
3. Product Goals
Goal 1

Detect meaningful deployment-related risks.

Goal 2

Explain why each risk exists.

Goal 3

Provide actual repository evidence.

Goal 4

Suggest actionable fixes.

Goal 5

Demonstrate genuine agentic AI rather than one LLM call.

Goal 6

Automatically run on GitHub changes.

Goal 7

Give a visual, professional developer experience.

4. Non-goals

Do not attempt to build:

a replacement for Kubernetes
a full CI/CD platform
a full vulnerability scanner
a complete static-analysis engine
an automatic production deployment system
a guarantee of "safe deployment"
an autonomous coding bot that changes production code automatically

DeploySafe should be an analysis and decision-support system.

5. Target Users
Persona A — Developer

Needs:

"I changed some files. Is anything risky before I merge?"

Persona B — DevOps / CI engineer

Needs:

"Can I put an AI deployment-risk check into my pipeline?"

Persona C — Student/professor evaluator

Needs:

"Show me the agents, tools, RAG, reasoning, evidence and working system."

For your course, Persona C is especially important.

6. Core User Journey
1. Connect repository
        ↓
2. Select branch / commit / PR
        ↓
3. Start analysis
        ↓
4. DeploySafe indexes repository
        ↓
5. Agents analyze different areas
        ↓
6. Findings are validated
        ↓
7. Risk score calculated
        ↓
8. User sees findings
        ↓
9. User sees evidence + fix
        ↓
10. User fixes code
        ↓
11. Push again
        ↓
12. DeploySafe re-runs
        ↓
13. Risk comparison shown
7. Core Product Architecture
                     ┌──────────────────────┐
                     │      Web UI          │
                     │ React + TypeScript   │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │      FastAPI         │
                     │    API Gateway       │
                     └──────────┬───────────┘
                                │
                                ▼
                  ┌───────────────────────────┐
                  │      CrewAI Flow          │
                  │      Orchestrator         │
                  └────────────┬──────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
       Code Agent        Dependency Agent   Config Agent
            │                  │                  │
            ▼                  ▼                  ▼
       Test Agent        Security Agent      RAG Agent
            │                  │                  │
            └──────────────────┼──────────────────┘
                               ▼
                       Critic Agent
                               │
                               ▼
                       Risk Engine
                               │
                               ▼
                       Report Agent
                               │
                               ▼
                     Deployment Report
8. Agent Design
Agent 1 — Orchestrator Agent
Responsibility

Control the complete workflow.

Input
repository metadata
changed files
analysis configuration
Output

Analysis plan.

Example:

{
  "run_code_analysis": true,
  "run_dependency_analysis": true,
  "run_config_analysis": true,
  "run_test_analysis": true,
  "run_rag_analysis": true
}
Agent 2 — Code Analysis Agent

Checks:

changed code
risky patterns
error handling
hard-coded configuration
breaking-change indicators
deployment-sensitive modifications

Must produce:

finding
severity
confidence
file
line
evidence
impact
recommendation
Agent 3 — Dependency Agent

Checks:

added packages
removed packages
version changes
conflicts
risky dependencies

Use deterministic scanners where possible and LLM reasoning only for interpretation.

Agent 4 — Configuration Agent

Checks:

.env
YAML
JSON
Docker
CI/CD configuration
environment variables
production settings
Agent 5 — Test Agent

Checks:

changed code vs relevant tests
test presence
test execution results
failed tests
missing regression tests

Do not claim:

"The application has complete test coverage."

Instead report measurable facts.

Agent 6 — Security Agent

Use deterministic tools first.

Possible tools:

Gitleaks
Semgrep OSS
Bandit for Python
OSV-Scanner
Trivy where relevant

The LLM then explains the findings.

Agent 7 — RAG/Documentation Agent

Uses repository knowledge:

README
Architecture docs
Deployment docs
CONTRIBUTING
config docs
runbooks

to answer:

"Does this change comply with this repository's own documented requirements?"

Agent 8 — Critic Agent

Reviews findings.

Its job:

Is the finding:
- supported?
- duplicated?
- relevant?
- correctly classified?
- backed by evidence?

Possible result:

VALID
WEAK_EVIDENCE
DUPLICATE
FALSE_POSITIVE_CANDIDATE
Agent 9 — Report Agent

Creates:

executive summary
risk score
findings
evidence
recommendations
deployment readiness
agent execution summary
9. Important Product Principle
Deterministic tools find facts.
Agents interpret facts.
RAG provides project context.
Critic validates AI findings.
Risk engine calculates score.

This is much stronger than:

Repository → ChatGPT → random score
10. Risk Engine

The LLM should not directly decide the final score.

Use a separate scoring service.

Example project-defined scoring:

Critical = 35
High     = 25
Medium   = 15
Low      = 7

Adjust using confidence and impact.

Example:

Finding score =
severity weight × confidence × scope multiplier

Then:

0–24     Low
25–49    Moderate
50–74    High
75–100   Critical

These thresholds are DeploySafe's own scoring policy, not an industry-standard safety guarantee.

11. Finding Schema

Every finding should use a structured schema.

{
  "id": "F-102",
  "category": "CONFIGURATION",
  "severity": "HIGH",
  "confidence": 0.91,
  "title": "Production configuration is hard-coded",
  "summary": "...",
  "repository": "...",
  "commit_sha": "...",
  "file_path": "config.yaml",
  "line_start": 12,
  "line_end": 12,
  "evidence": "...",
  "impact": "...",
  "recommendation": "...",
  "source_type": "deterministic+agent",
  "agent": "config_agent",
  "status": "validated"
}
12. RAG Requirements
Ingestion

Repository:

↓
file discovery
↓
ignore binary/vendor/generated files
↓
language detection
↓
chunking
↓
metadata
↓
embeddings
↓
Chroma
Metadata

Each chunk should include:

repository
commit
file path
language
chunk type
line start
line end

This enables evidence such as:

config.yaml:12–18

instead of vague AI explanations.

13. RAG Rules

Never allow:

"I think the repository does X."

without supporting context.

Prompt agents to return:

Evidence available: YES/NO

When evidence is insufficient:

Insufficient repository evidence.

This is one of your most important anti-hallucination mechanisms.

14. Tool Layer

Create tools such as:

get_repository_files()
get_file_content()
get_git_diff()
get_commit_metadata()
get_dependency_manifest()
run_tests()
run_gitleaks()
run_semgrep()
run_osv_scan()
run_bandit()
run_trivy()
search_repository_knowledge()

Every tool should:

have typed inputs
have typed outputs
have timeout
return errors clearly
write execution logs
never expose secrets
15. GitHub Integration
Midterm

Support:

GitHub URL

or local repository upload.

End-term

Support:

Pull Request
    ↓
GitHub Action
    ↓
DeploySafe

Recommended triggers:

on:
  pull_request:
  push:
    branches:
      - main
16. GitHub Action behavior
PR opened/updated
      ↓
Start DeploySafe
      ↓
Fetch diff
      ↓
Analyze repository
      ↓
Generate report
      ↓
Publish result

Optional final-stage behavior:

Risk < threshold → PASS
Risk >= threshold → REVIEW REQUIRED

Don't make automatic deployment the default.

17. UI / UX PRD

This is where you should aim higher than a normal college project.

Design direction
Feel

Professional developer-security platform

Not:

generic AI chatbot
colorful student dashboard
giant gradients everywhere
excessive cards
unnecessary animations
Visual inspiration

Build an original interface with the clarity of modern developer products:

strong typography
generous spacing
restrained visual hierarchy
subtle borders
compact data density
clear status states
excellent code/evidence presentation
18. UI Structure
Left navigation
DeploySafe

Overview
Analyze
Repositories
Runs
Findings
Agents
Reports
Settings
19. Dashboard

Top area:

Repository
Production API

Branch
main

Latest Analysis
#284

Main metrics:

Risk Score       68
Risk Level       HIGH
Findings         9
Validated        7
Critical         1

Then:

Risk distribution
Critical █
High     ███
Medium   ████
Low      ██
Recent run
Run #284

Repository analyzed
87 files

Agents
8/8 completed

RAG
143 chunks retrieved

Duration
42.3s
20. Findings screen

Each finding:

HIGH
Production DB configuration risk

config.yaml
Lines 12–15

Evidence
...

Why this matters
...

Recommended fix
...

Found by
Configuration Agent

Validated by
Critic Agent

Add:

"Open in code"

21. Run Details screen

This should be one of your best screens.

Analysis #284

HIGH
Risk Score 68

Timeline:

10:41:01  Repository ingestion    ✓
10:41:05  Code agent              ✓
10:41:08  Dependency agent        ✓
10:41:10  Config agent            ✓
10:41:13  Test agent              ✓
10:41:17  RAG agent               ✓
10:41:24  Critic                  ✓
10:41:29  Risk engine             ✓
10:41:31  Report generated        ✓

This directly helps demonstrate orchestration/observability.

22. Agent Activity Screen

Show:

ORCHESTRATOR
Planning analysis...

CODE AGENT
Analyzing 23 changed files...

CONFIG AGENT
Scanning 8 configuration files...

RAG AGENT
Retrieved 7 relevant documentation chunks...

CRITIC
Reviewing 11 findings...

This is excellent for your professor demo.

23. Before / After screen

Very important.

Previous run       Current run

Risk: HIGH         Risk: MODERATE

9 findings         5 findings

1 critical         0 critical

Show what changed.

This gives your product a strong real-world story.

24. UX details

Use:

keyboard-friendly navigation
responsive layout
accessible contrast
tooltips for technical terms
skeleton loading
clear empty states
clear error states
no fake progress bars
real-time run status
copyable evidence
downloadable report
25. Product Security

DeploySafe itself must be secure.

Never:
API key in source code
GitHub token in frontend
raw secret in LLM prompt
Use:
.env
server-side secrets
secret redaction
Before sending repository content to LLM:
repository
 ↓
secret detection
 ↓
redaction
 ↓
LLM

Also tell the user in Settings:

Repository content may be sent to the configured model provider for analysis.

That is transparent and academically defensible.

26. Observability

Every run should produce:

run_id
agent
start_time
end_time
status
tool_calls
retrieval_count
finding_count
model
errors

This allows the UI to show real execution.

27. Evaluation Strategy

Create a DeploySafe Evaluation Repository.

It should contain intentionally seeded issues.

Example:

repo/
 ├── secret_issue/
 ├── dependency_issue/
 ├── config_issue/
 ├── test_issue/
 ├── docker_issue/
 └── documentation_issue/

For every test repository, define expected findings.

Measure:

Detection rate
False positive rate
Evidence correctness
Severity agreement
Recommendation usefulness
Runtime

Do not claim scientific benchmark-level accuracy from a small student dataset.

28. Functional Requirements
FR-01

User can connect repository.

FR-02

System can inspect supported repository files.

FR-03

System can compute git diff.

FR-04

System indexes repository knowledge.

FR-05

System runs multiple agents.

FR-06

Agents can use tools.

FR-07

System generates structured findings.

FR-08

Every AI finding must have evidence or explicitly state insufficient evidence.

FR-09

System validates findings.

FR-10

System calculates risk score separately.

FR-11

System generates report.

FR-12

System stores run history.

FR-13

System shows agent execution trace.

FR-14

GitHub Action can trigger analysis.

FR-15

User can compare runs.

29. Non-functional Requirements
Reliability

A failed agent should not crash the complete system where possible.

Performance

For demo repositories:

target 30–120 seconds for complete analysis.

That is a project target, not a guaranteed benchmark.

Security

No secrets stored client-side.

Explainability

Every finding has evidence.

Maintainability

Agents, tools and scoring must be separate modules.

Cost

Design for free/open-source components.

30. Folder Architecture
deploysafe/
│
├── backend/
│   ├── api/
│   ├── agents/
│   ├── crews/
│   ├── flows/
│   ├── tools/
│   ├── rag/
│   ├── scoring/
│   ├── scanners/
│   ├── models/
│   ├── services/
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── features/
│   │   ├── hooks/
│   │   └── lib/
│
├── demo-repos/
│
├── .github/
│   └── workflows/
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── agents.md
│   ├── rag.md
│   ├── risk-model.md
│   └── demo-script.md
│
├── docker/
│
├── .env.example
├── docker-compose.yml
├── README.md
└── LICENSE
31. PHASE PLAN

You asked for 6 phases × 8 parts.

PHASE 1 — FOUNDATION & PRODUCT SETUP
Part 1 — Freeze scope

Define:

problem
users
MVP
non-goals
midterm target
end-term target
Part 2 — Architecture

Create:

Frontend
Backend
CrewAI
LLM
RAG
Tools
GitHub
Database
Part 3 — Repository setup

Create GitHub repository with:

README
.gitignore
.env.example
branch structure
issue templates
Part 4 — Backend skeleton

Implement:

FastAPI
health endpoint
config
logging
database
Part 5 — Frontend skeleton

Implement:

sidebar
top bar
dashboard shell
routing
theme
design tokens
Part 6 — LLM abstraction

Create:

LLMProvider

with:

GeminiProvider
GroqProvider

so provider can be swapped.

Part 7 — First CrewAI workflow

Create:

Flow
 ↓
one agent
 ↓
structured output
Part 8 — Phase gate

Must have:

app starts
API works
UI works
LLM responds
CrewAI workflow works
no API key hardcoded
PHASE 2 — REPOSITORY INGESTION + RAG
Part 1 — Repository loader

Support:

GitHub URL
local path
ZIP
Part 2 — File discovery

Detect:

Python
JavaScript
TypeScript
Java
Go
YAML
JSON
Docker
Markdown
Part 3 — Ignore rules

Ignore:

.git
node_modules
venv
dist
build
binary files
large generated files
Part 4 — Intelligent chunking

Chunk around:

functions
classes
sections
config blocks
documentation sections
Part 5 — Embeddings

Use:

Gemini Embedding 2

with a local embedding fallback.

Part 6 — Chroma

Store embeddings with metadata.

Part 7 — Retrieval tool

Build:

search_repository_knowledge(query)
Part 8 — Phase gate

Demo:

Repository
 ↓
Chunks
 ↓
Embeddings
 ↓
Chroma
 ↓
Query
 ↓
Relevant repository context

This is your first strong RAG demonstration.

PHASE 3 — CORE AGENTIC ANALYSIS
Part 1 — Orchestrator

Build the CrewAI Flow.

Part 2 — Code Agent

Implement structured analysis.

Part 3 — Dependency Agent

Implement manifest analysis.

Part 4 — Configuration Agent

Implement YAML/env/Docker/CI checks.

Part 5 — Test Agent

Run/read tests.

Part 6 — RAG Agent

Use repository documentation.

Part 7 — Critic Agent

Validate findings.

Part 8 — Midterm gate

This is the target midterm build.

Live demo:

GitHub repository
 ↓
Orchestrator
 ↓
4–6 agents
 ↓
RAG
 ↓
Findings
 ↓
Basic risk report

The course's Phase-2 explicitly expects a working prototype/code demonstration.

PHASE 4 — RISK ENGINE + PROFESSIONAL UI
Part 1 — Finding schema

Standardize all outputs.

Part 2 — Deduplication

Merge duplicate findings.

Part 3 — Severity

Implement:

Critical
High
Medium
Low
Part 4 — Confidence

Add:

High
Medium
Low

or numeric confidence internally.

Part 5 — Risk score

Calculate deterministic score.

Part 6 — Report generation

Create:

JSON
HTML
Markdown
Part 7 — UI

Build:

dashboard
run page
finding details
agent activity
report page
Part 8 — UX polish

Add:

loading
empty states
error states
responsive layout
animations only where useful
PHASE 5 — GITHUB AUTOMATION + SAFETY + EVALUATION
Part 1 — GitHub Action

Trigger on PR.

Part 2 — PR metadata

Collect:

PR number
branch
commit
changed files
author
Part 3 — Pipeline integration
GitHub
 ↓
Action
 ↓
DeploySafe API
Part 4 — Guardrails

Implement:

secret redaction
tool permissions
command allowlist
execution timeout
model fallback
Part 5 — Observability

Track:

run
agent
tool
latency
error
finding
Part 6 — Evaluation dataset

Create seeded risky repositories.

Part 7 — Measure

Track:

true positives
false positives
evidence correctness
runtime
Part 8 — Phase gate

A GitHub PR should automatically produce:

DeploySafe Analysis
Risk: HIGH
Findings: 7
PHASE 6 — ENDTERM HARDENING + DEMO
Part 1 — Reliability

Handle:

API failure
agent failure
timeout
empty repo
unsupported files
LLM quota
Part 2 — Provider fallback
Gemini
 ↓ fails
Groq
Part 3 — Run comparison
Before
vs
After
Part 4 — Final report

Include:

architecture
agents
tools
RAG
scoring
evaluation
limitations
Part 5 — Demo repository

Create deterministic demo risks.

Part 6 — Final UI polish

Everything should feel like one product.

Part 7 — Deployment

Dockerize and deploy.

Part 8 — End-term gate

Final demo:

PR created
 ↓
GitHub Action
 ↓
DeploySafe
 ↓
Agents
 ↓
RAG
 ↓
Critic
 ↓
Score
 ↓
Report
 ↓
Fix issue
 ↓
Push again
 ↓
Risk improves

This aligns with the handout's final requirement for a functional agentic application, GitHub repository, report, presentation/demo and viva.

32. MIDTERM SCOPE — DO NOT OVERBUILD

Your midterm should not contain everything.

Midterm must have
✅ Repository ingestion
✅ RAG
✅ CrewAI
✅ Orchestrator
✅ 3–5 useful agents
✅ At least 3 tools
✅ Structured findings
✅ Basic risk scoring
✅ Working UI
✅ Live demo
Save for endterm
→ GitHub Actions
→ Critic refinement
→ Advanced security scanning
→ Observability
→ Run comparison
→ Provider fallback
→ polished reports
33. ENDTERM SCOPE
✅ Multi-agent
✅ RAG
✅ Tool calling
✅ Reflection
✅ Deterministic scanners
✅ Risk engine
✅ GitHub Actions
✅ Dashboard
✅ Agent trace
✅ Evaluation
✅ Guardrails
✅ Report generation
✅ Before/after analysis
✅ Docker deployment

That directly covers many of the course areas: orchestration, tools, state/memory, multi-agent workflows, guardrails, evaluation, observability and deployment.

34. Live Demo Script

This is the demo I would rehearse exactly.

Step 1

Open DeploySafe dashboard.

Step 2

Connect demo repository.

Step 3

Show repository summary.

87 files
Python
Docker
YAML
Tests
README
Step 4

Click:

Analyze Repository

Step 5

Show live agent activity.

Orchestrator       ✓
Code Agent         ✓
Config Agent       ✓
Dependency Agent   ✓
Test Agent         ✓
RAG Agent          ✓
Critic             ✓
Reporter           ✓
Step 6

Show result.

RISK SCORE: 72
RISK LEVEL: HIGH
Step 7

Open finding.

HIGH
Production configuration issue

File:
config.yaml

Lines:
12–15

Evidence:
...

Impact:
...

Recommendation:
...
Step 8

Open agent trace.

Step 9

Open RAG evidence.

Step 10

Fix the repository issue.

Step 11

Push commit.

Step 12

GitHub Action starts automatically.

Step 13

Show second result.

BEFORE
72 HIGH

AFTER
38 MODERATE

That is a very strong final demo story.

35. What makes this project genuinely Agentic

Your professor may ask:

"Why is this Agentic AI and not simply an LLM application?"

Your answer:

1. The workflow is planned dynamically.
2. Multiple specialized agents collaborate.
3. Agents use external tools.
4. Agents retrieve repository knowledge.
5. One agent critiques another's findings.
6. Outputs are passed between agents.
7. The system maintains run state.
8. The workflow is observable and evaluable.

That maps closely to the course's stated emphasis on planning, reasoning, tool use, reflection and multi-agent workflows.

36. Important academic-integrity point

Your handout explicitly says AI-generated code/plagiarism can be treated under the university's unfair-means policy, and students are expected to understand and be able to explain and modify project components during evaluation.

So the master prompt below explicitly tells Antigravity:

Generate code, but also generate explanations, tests, architecture documentation and implementation decisions so the team can understand the system.

MASTER PROMPT FOR GOOGLE ANTIGRAVITY

Paste this into your Antigravity project as the master build instruction.

You are the principal engineer, product architect, AI systems architect, senior UX engineer, QA lead, DevOps engineer, and technical project manager responsible for building the complete DeploySafe product.

PROJECT NAME
DeploySafe

PROJECT TAGLINE
Know the deployment risk before you deploy.

PROJECT PURPOSE
Build a production-style academic prototype of a multi-agent AI deployment-readiness platform that analyzes software repositories, code changes, dependencies, configuration files, tests, deployment files, and project documentation.

DeploySafe must use:
- multi-agent orchestration
- LLM reasoning
- repository RAG
- tool calling
- structured agent outputs
- critic/reflection
- deterministic risk scoring
- GitHub integration
- GitHub Actions
- guardrails
- evaluation
- monitoring/observability
- explainable reporting

IMPORTANT PRODUCT POSITIONING
DeploySafe is NOT a CI/CD replacement.
CI/CD executes software delivery workflows.
DeploySafe is an AI-powered risk-analysis layer that helps developers understand potential deployment risks before release.

PRIMARY COURSE REQUIREMENTS
The project must visibly demonstrate:
- LLMs
- Agentic AI
- CrewAI
- multi-agent orchestration
- planning
- tool use
- RAG
- reflection/criticism
- guardrails
- evaluation
- deployment
- observability

TECHNOLOGY CONSTRAINTS
Use free/open-source technologies whenever practical.

PRIMARY STACK
- Python
- FastAPI
- CrewAI
- React
- TypeScript
- Tailwind CSS
- shadcn/ui or equivalent open-source component system
- SQLite
- Chroma
- Docker
- GitHub Actions
- OpenTelemetry
- Gemini API
- Groq API as fallback

LLM
Primary:
gemini-3.8-flash

Fallback:
Groq openai/gpt-oss-120b

EMBEDDINGS
Primary:
gemini-embedding-2

Fallback:
local sentence-transformers embedding model

DO NOT hardcode API keys.

Read keys from environment variables:
GEMINI_API_KEY
GROQ_API_KEY
GITHUB_TOKEN
DATABASE_URL
CHROMA_PATH
APP_ENV

Create:
.env.example

Never commit:
.env
credentials
tokens
private keys

PRODUCT PRINCIPLES

1. No bluffing.
Never claim that a risk exists without evidence.
Never invent a file path.
Never invent line numbers.
Never invent test results.
Never invent scanner results.
Never say a repository is safe with absolute certainty.

2. Evidence first.
Every finding must have evidence.
If evidence cannot be established, mark:
INSUFFICIENT_EVIDENCE

3. Deterministic checks before LLM interpretation.
Use deterministic tools for facts wherever possible.
Use the LLM to reason, correlate, prioritize, explain, and recommend.

4. Structured outputs.
All agents must return typed structured outputs using Pydantic or equivalent schemas.

5. Risk score is deterministic.
The LLM does not directly decide the final score.

6. Failure isolation.
If one agent fails, preserve partial results where possible and continue safely.

7. Provider abstraction.
The application must allow switching between Gemini and Groq.

8. Demo reliability.
The application must include deterministic demo repositories with seeded problems.

9. Academic understanding.
Every major module must have clear documentation explaining:
- what it does
- why it exists
- how it works
- how to test it
- common failure modes

10. Do not over-engineer.
Prefer a smaller working system over a huge incomplete system.

==================================================
PHASE MANAGEMENT
==================================================

Build the project in exactly six major phases.

DO NOT implement all six phases in one uncontrolled operation.

At the beginning of each phase:
1. inspect existing project
2. inspect previous phase artifacts
3. identify what already works
4. create a short implementation plan
5. identify dependencies
6. implement the phase
7. run tests
8. run the application
9. verify via browser where possible
10. produce a phase completion report

Do not silently move to the next phase until the current phase reaches its definition of done.

If a feature is too large:
- create a minimal working version first
- document future improvements
- continue

==================================================
PHASE 1 — FOUNDATION
==================================================

PART 1 — SCOPE
Create:
docs/product-scope.md

Include:
- problem
- users
- goals
- non-goals
- MVP
- midterm scope
- endterm scope

PART 2 — ARCHITECTURE
Create:
docs/architecture.md

Include:
- component architecture
- data flow
- agent architecture
- RAG architecture
- API architecture
- UI architecture
- deployment architecture

Create an architecture diagram.

PART 3 — REPOSITORY
Create:
- README.md
- .gitignore
- .env.example
- project documentation
- standard source layout

PART 4 — BACKEND
Create FastAPI application with:
- health endpoint
- configuration loading
- structured logging
- database initialization
- error handling
- API versioning

PART 5 — FRONTEND
Create:
- application shell
- navigation
- dashboard placeholder
- theme system
- reusable components
- loading/error/empty states

PART 6 — MODEL ABSTRACTION
Create a provider interface:
LLMProvider

Implement:
GeminiProvider
GroqProvider

Requirements:
- retries
- timeout
- provider fallback
- structured output support
- error handling

PART 7 — FIRST AGENT
Create minimal CrewAI Flow:
Flow
→ agent
→ structured result

PART 8 — TESTING
Add:
- backend startup test
- provider configuration test
- agent invocation test
- frontend build test

PHASE 1 DEFINITION OF DONE
The application starts.
The backend responds.
The frontend loads.
CrewAI runs.
At least one LLM call works.
No secrets are hardcoded.
Documentation exists.
Tests pass.

==================================================
PHASE 2 — REPOSITORY ANALYSIS + RAG
==================================================

PART 1 — REPOSITORY LOADER
Implement:
- GitHub URL ingestion
- local repository ingestion
- optional ZIP ingestion

PART 2 — FILE DISCOVERY
Detect common:
- Python
- JavaScript
- TypeScript
- Java
- Go
- YAML
- JSON
- Markdown
- Docker
- shell scripts

Add configurable ignore rules.

PART 3 — SAFE INGESTION
Ignore:
- .git
- node_modules
- venv
- build
- dist
- binary files
- giant generated files

Set maximum file sizes.
Set maximum number of indexed files.

PART 4 — CHUNKING
Implement repository-aware chunking.
Prefer semantic boundaries where practical.

Each chunk must retain:
- path
- language
- line_start
- line_end
- commit_sha
- chunk_type

PART 5 — EMBEDDINGS
Implement Gemini Embedding 2.
Add local embedding fallback.

PART 6 — CHROMA
Store vectors in Chroma.

Implement:
- create collection
- upsert
- search
- metadata filtering
- delete/reindex

PART 7 — RAG TOOL
Implement:
search_repository_knowledge(query)

It must return:
- chunk
- score
- file_path
- line range
- metadata

PART 8 — RAG TESTING
Create test repository.
Test:
question
→ retrieval
→ evidence

PHASE 2 DEFINITION OF DONE
A repository can be indexed.
The vector database contains chunks.
Queries return relevant repository evidence.
Metadata includes file and line information.
RAG works without hallucinated citations.

==================================================
PHASE 3 — CORE MULTI-AGENT DEPLOYSafe
==================================================

Create these agents:

1. Orchestrator Agent
2. Code Analysis Agent
3. Dependency Agent
4. Configuration Agent
5. Test Agent
6. Documentation/RAG Agent
7. Security Analysis Agent
8. Critic Agent
9. Report Agent

IMPORTANT:
Do not create artificial agents that exist only for presentation.
Every agent must have a real responsibility.

PART 1 — ORCHESTRATOR
Implement CrewAI Flow responsible for:
- run creation
- state
- task ordering
- parallel execution where safe
- error capture
- final aggregation

PART 2 — CODE AGENT
Analyze:
- changed files
- dangerous patterns
- hard-coded configuration
- exception handling
- deployment-sensitive code
- potential breaking changes

PART 3 — DEPENDENCY AGENT
Analyze:
- dependency manifests
- added dependencies
- removed dependencies
- version changes
- known scanner outputs
- conflicts

PART 4 — CONFIG AGENT
Analyze:
- .env examples
- YAML
- JSON
- Docker
- GitHub Actions
- production configuration

PART 5 — TEST AGENT
Analyze:
- test files
- changed modules
- test execution
- failures
- missing tests

Do not claim actual coverage unless measured.

PART 6 — SECURITY AGENT
Integrate deterministic tools where available:
- Gitleaks
- Semgrep
- Bandit
- OSV-Scanner
- Trivy when applicable

Use scanners as evidence generators.
Use LLM to interpret findings.

PART 7 — RAG + CRITIC
RAG agent:
- retrieve relevant repository documentation
- compare changes against repository-specific context

Critic:
- validate evidence
- detect duplicates
- downgrade unsupported findings
- identify weak evidence
- identify false-positive candidates

PART 8 — STRUCTURED FINDING OUTPUT
Create a canonical Finding model:
- id
- category
- severity
- confidence
- title
- summary
- impact
- recommendation
- file path
- line range
- evidence
- source
- agent
- status

PHASE 3 DEFINITION OF DONE
At least four agents work together.
RAG is used.
Tools are used.
Findings are structured.
Critic validates findings.
A report is generated.

This is the MIDTERM-CAPABLE BUILD.

==================================================
PHASE 4 — RISK ENGINE + UI
==================================================

PART 1 — RISK ENGINE
Create deterministic scoring service.

Default weights:
Critical = 35
High = 25
Medium = 15
Low = 7

Combine with:
- confidence
- impact
- scope

Normalize to 0–100.

Levels:
0–24 Low
25–49 Moderate
50–74 High
75–100 Critical

Clearly document that these are DeploySafe project-defined thresholds.

PART 2 — DEDUPLICATION
Prevent multiple agents reporting the same issue repeatedly.

PART 3 — FINDING MANAGEMENT
Support statuses:
- New
- Validated
- Needs Review
- Duplicate
- Dismissed

PART 4 — DASHBOARD
Create polished dashboard:
- risk score
- severity distribution
- latest run
- findings summary
- repository overview
- trend

PART 5 — RUN DETAIL
Show:
- run metadata
- agent timeline
- tool calls
- RAG retrieval count
- findings
- execution duration
- errors

PART 6 — FINDING DETAIL
Show:
- severity
- confidence
- file
- lines
- evidence
- why it matters
- recommendation
- validating agent
- source tools

PART 7 — AGENT ACTIVITY
Show realistic live execution:
- orchestrator
- agent status
- tool calls
- RAG activity
- critic
- report generation

Never fake progress.
UI status must come from real backend events.

PART 8 — DESIGN POLISH
Use a premium developer-product visual language:
- precise spacing
- excellent typography
- restrained palette
- subtle borders
- clean cards
- professional tables
- code viewer
- keyboard accessibility
- responsive design
- useful micro-interactions
- no unnecessary gradients
- no generic chatbot appearance

PHASE 4 DEFINITION OF DONE
UI feels like a professional developer/security product.
Runs can be viewed.
Findings can be inspected.
Risk score is deterministic.
Agent activity is visible.

==================================================
PHASE 5 — GITHUB ACTIONS + SAFETY + EVALUATION
==================================================

PART 1 — GITHUB INTEGRATION
Support repository metadata and:
- branch
- commit
- pull request
- changed files

PART 2 — GITHUB ACTION
Create workflow:
pull_request
push

Flow:
GitHub
→ GitHub Action
→ DeploySafe
→ analysis
→ result

PART 3 — PR SUMMARY
Generate:
- risk score
- finding counts
- top risks
- report link

PART 4 — GUARDRAILS
Implement:
- secret redaction
- execution timeout
- tool allowlist
- command allowlist
- repository size limits
- prompt injection defense
- malformed LLM output handling

PART 5 — MODEL FALLBACK
Primary:
Gemini

Fallback:
Groq

Do not endlessly retry.
Handle 429 gracefully.

PART 6 — OBSERVABILITY
Implement:
- structured logs
- run IDs
- agent IDs
- tool execution timing
- failures
- retrieval counts
- model provider
- final status

Use OpenTelemetry where practical.

PART 7 — EVALUATION REPOSITORIES
Create deterministic demo repositories:
- hard-coded secret
- config problem
- dependency issue
- missing regression test
- Docker problem
- documentation mismatch

For each, define expected findings.

PART 8 — EVALUATION METRICS
Measure:
- detection rate
- false positive rate
- evidence correctness
- severity agreement
- recommendation usefulness
- runtime

Do not fake benchmark results.

PHASE 5 DEFINITION OF DONE
A PR automatically triggers DeploySafe.
The UI receives the run.
Findings appear.
GitHub receives a result.
Guardrails work.
Evaluation dataset exists.
Observability works.

==================================================
PHASE 6 — FINAL PRODUCT + ENDTERM
==================================================

PART 1 — RELIABILITY
Test:
- empty repository
- unsupported language
- API timeout
- LLM failure
- scanner failure
- malformed response
- rate limit
- very large file
- no findings

PART 2 — BEFORE/AFTER
Implement run comparison:
- previous score
- current score
- finding delta
- resolved issues
- newly detected issues

PART 3 — FINAL REPORT
Create:
Markdown
HTML
JSON

Report sections:
- executive summary
- repository summary
- risk score
- finding breakdown
- evidence
- recommendations
- agent activity
- limitations

PART 4 — FINAL DEMO DATASET
Create one polished demo repository that gives:
- one critical
- two high
- several medium/low
findings.

Do not randomly generate the demo.

PART 5 — DEPLOYMENT
Dockerize:
- frontend
- backend
- database
- vector store

Provide local docker-compose.

Provide a simple deployment guide.

PART 6 — UI FINAL POLISH
Check:
- spacing
- typography
- responsive layout
- empty states
- errors
- accessibility
- browser consistency
- no broken buttons
- no placeholder text
- no dead navigation links

PART 7 — DOCUMENTATION
Create:
- README
- architecture
- agents
- tools
- RAG
- scoring
- evaluation
- security
- deployment
- demo script
- limitations

PART 8 — FINAL ENDTERM VALIDATION
Perform an end-to-end test:

Create PR
→ GitHub Action
→ DeploySafe
→ repository analysis
→ deterministic scanners
→ agents
→ RAG
→ critic
→ risk engine
→ report
→ GitHub result
→ UI run
→ finding inspection
→ fix issue
→ push again
→ second analysis
→ before/after comparison

==================================================
AGENT BEHAVIOR RULES
==================================================

ALL AGENTS MUST:

- stay within role
- use tools instead of guessing
- cite evidence
- use structured output
- distinguish observed facts from inference
- say insufficient evidence when necessary
- avoid duplicate findings
- avoid absolute claims
- never expose secrets
- never fabricate line numbers
- never fabricate scanner outputs
- never fabricate test results

==================================================
CODE QUALITY RULES
==================================================

- typed Python
- type-safe TypeScript
- modular architecture
- small functions
- clear names
- docstrings on important functions
- environment-based configuration
- robust exception handling
- unit tests
- integration tests
- no dead code
- no massive files unless justified
- no duplicated business logic

==================================================
UX RULES
==================================================

The interface must feel like a serious developer tool.

Avoid:
- student-project aesthetics
- oversized rounded cards
- excessive gradients
- excessive color
- meaningless animations
- fake AI animations
- chatbot-first layout

Prioritize:
- information hierarchy
- clarity
- speed
- evidence visibility
- professional typography
- excellent code reading experience
- traceability
- confidence
- accessible interaction

==================================================
ANTI-HALLUCINATION RULES
==================================================

Every AI-generated finding must include:

1. finding statement
2. evidence
3. evidence location
4. impact
5. recommendation
6. confidence
7. source

If any critical part is missing:
mark:
INSUFFICIENT_EVIDENCE

Never invent missing information.

==================================================
SECRETS RULE
==================================================

Before sending repository snippets to an external LLM:

1. identify probable secrets
2. redact them
3. preserve enough structural context
4. log that redaction happened
5. never expose original secret to frontend

==================================================
DEMO RULE
==================================================

The demo must be deterministic.

Maintain:
demo-repos/

Every demo repository must document:
- expected risks
- expected files
- expected severity
- expected evidence

This ensures the professor demo does not depend on luck.

==================================================
ANTIGRAVITY WORKFLOW
==================================================

Use Antigravity effectively.

At every major step:
- create a plan artifact
- implement
- run tests
- use browser verification
- inspect visual results
- create a walkthrough artifact
- report files changed
- report tests run
- report known limitations

Use the browser to inspect the actual application.
Do not assume the UI looks correct from source code.

When a feature is complete:
- test API
- test frontend
- test integration
- inspect browser
- fix visible issues

==================================================
BEFORE STARTING EACH PHASE
==================================================

First inspect:
- current directory
- existing code
- existing dependencies
- README
- environment configuration
- tests
- previous phase documentation

Then tell yourself:
1. what already exists
2. what must be built
3. what can be reused
4. what must not be changed
5. what dependencies are needed

Do not rewrite working modules unnecessarily.

==================================================
DELIVERY ARTIFACTS
==================================================

Maintain these documents:

docs/
├── product-scope.md
├── architecture.md
├── agents.md
├── tools.md
├── rag.md
├── risk-model.md
├── security.md
├── evaluation.md
├── deployment.md
├── demo-script.md
└── decisions.md

Also maintain:
CHANGELOG.md

Each phase must update:
CHANGELOG.md

==================================================
FINAL SUCCESS CRITERIA
==================================================

DeploySafe is considered successful only when a real user can:

1. connect a repository
2. start an analysis
3. watch the agent workflow
4. inspect findings
5. open evidence
6. understand why the risk exists
7. read a recommended fix
8. view the calculated risk score
9. inspect the RAG evidence
10. inspect agent execution
11. trigger analysis from GitHub
12. compare analysis runs
13. download a report

The complete system must be demonstrable live.

==================================================
IMPORTANT
==================================================

Do not optimize for the number of features.

Optimize for:
- working software
- correct outputs
- evidence
- agentic behavior
- strong UX
- explainability
- reliability
- demonstrability

Never fake functionality.

If a feature cannot be implemented reliably:
- implement the smallest real version
- document the limitation
- do not simulate success.

At the end of each phase, provide:
PHASE STATUS
- Implemented
- Tested
- Browser verified
- Known issues
- Next phase
37. One change I strongly recommend

For the best technical credibility, don't make this:

LLM → find everything

Make it:

                    DeploySafe
                        │
              ┌─────────┴─────────┐
              │                   │
       Deterministic         Agentic Analysis
          Tools                     │
       ┌────┼────┐             ┌────┼────┐
    Gitleaks   OSV          Code  Config  RAG
    Semgrep    Tests         │      │      │
       └────┬───────────────┴──────┴──────┘
            │
            ▼
        Critic Agent
            │
            ▼
        Risk Engine
            │
            ▼
      Final Explanation

That makes your project much easier to defend in viva because you can say:

"Tools provide observable evidence; agents reason over that evidence; RAG adds project context; critic validates it; the risk engine produces the final score."

That is a much stronger architecture than letting an LLM invent the whole result.

38. Your exact final product story
MIDTERM

"Give DeploySafe a repository. Our CrewAI agents analyze its code, dependencies, configuration and tests, use RAG to understand project documentation, and produce an evidence-backed deployment-risk report."

ENDTERM

"When a developer opens or updates a GitHub PR, GitHub Actions automatically runs DeploySafe. Its multi-agent workflow analyzes the change, uses deterministic tools and repository RAG, validates findings with a critic agent, calculates a risk score, and publishes an explainable deployment-readiness report. After the developer fixes the issue, DeploySafe re-runs and shows the before/after risk."