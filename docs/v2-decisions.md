# DeploySafe V2 — Design & Architecture Decisions (ADR)

## ADR-01: Deterministic Rule-Based Change Impact over Unbounded LLM Graph Inference

- **Context**: In Phase 7 Step 5, we considered whether to use an LLM prompt to guess architectural blast radius or use deterministic physical file path heuristics.
- **Decision**: Implemented deterministic pattern matching in `backend/app/services/change_impact.py`.
- **Rationale**:
  - LLMs frequently hallucinate nonexistent service dependencies or misjudge file scope.
  - Deterministic rules execute in under 10ms with zero API token cost and zero non-determinism.
  - Changes to database migrations, authentication, Dockerfiles, and CI workflows have well-known industry blast radii.
- **Consequences**: Fast, perfectly predictable blast radius determinations; 100% reproducible across CI/CD runs.

---

## ADR-02: Read-Only Remediation Patches with Mandatory Human Review

- **Context**: Phase 7 Step 16 proposed automated remediation proposals.
- **Decision**: Generated patches are strictly formatted as previewable unified diffs (`diff -u`) with explicit human approval disclaimers, rather than allowing agentic auto-commits to repositories.
- **Rationale**:
  - Automated code modification in production deployment pipelines introduces severe supply-chain risks.
  - Code fixes must be validated by human software engineers and pass CI integration tests before being merged.
- **Consequences**: Safe developer experience; zero risk of agent regressions or destructive file overwrites.

---

## ADR-03: Security Hardening & Fail-Safe Defaults for `deploysafe.yml`

- **Context**: Allowing repositories to supply their own configuration file (`deploysafe.yml`) creates risks of malicious directory traversal (e.g. `../../etc/passwd`) or arbitrary command execution.
- **Decision**: Enforced strict path normalization and traversal blocking in `RepoConfigService`, combined with Pydantic type validation for bounded integer ranges.
- **Rationale**:
  - Defense-in-depth against malicious repository payloads or poisoned pull requests.
  - If a file is malformed or invalid, the engine silently falls back to safe production defaults rather than crashing the analysis pipeline.
- **Consequences**: Safe ingestion of user-contributed configs across multi-tenant deployments.

---

## ADR-04: Multi-Run Historical Telemetry via Physical Analysis Storage

- **Context**: Tracking risk score trends and recurring issues across deployments.
- **Decision**: Queried historical runs from the physically persisted reports in memory/disk rather than relying on an external ephemeral cache.
- **Rationale**:
  - Guarantees historical consistency and true audit trails.
  - Enables offline analysis without relying on external SaaS tracking services.
- **Consequences**: Instant velocity and regression metrics with zero external network dependencies.
