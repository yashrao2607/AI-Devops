# Expected Findings Specification — deploysafe-analysis-demo

This document defines the ground-truth seeded deployment issues in `demo-repos/deploysafe-analysis-demo` for Phase 3 Multi-Agent evaluation.

---

### Issue 1: Hardcoded Local Network Endpoint in Source Code
- **File:** `src/payment.py` (Line 8)
- **Source of Truth:** `self.gateway_url = "http://localhost:8080/v1/charge"`
- **Expected Category:** `CODE`
- **Expected Severity:** `HIGH`
- **Detecting Agent:** `CodeAgent`
- **Why It Exists:** When deployed inside containers or cloud networks, `localhost` resolves to the local container loopback rather than the payment gateway, failing all customer transactions.

---

### Issue 2: Unpinned Dependency in Manifest
- **File:** `requirements.txt` (Line 4)
- **Source of Truth:** `requests`
- **Expected Category:** `DEPENDENCY`
- **Expected Severity:** `HIGH`
- **Detecting Agent:** `DependencyAgent`
- **Why It Exists:** Without a pinned version (`requests==x.y.z`), builds in CI/CD fetch the latest upstream package, risking breaking changes and build instability.

---

### Issue 3: Hardcoded Production Database Credentials
- **File:** `config/production.py` (Line 5)
- **Source of Truth:** `DATABASE_URI = "postgres://admin:SuperSecretPassword123!@db.prod.internal:5432/main"`
- **Expected Category:** `CONFIGURATION` & `SECURITY`
- **Expected Severity:** `CRITICAL`
- **Detecting Agents:** `ConfigAgent` & `SecurityAgent` (correlating secret and configuration risks)
- **Why It Exists:** Static credentials committed to version control violate security compliance and prevent environment-specific secret injection.

---

### Issue 4: Unpinned Container Base Image Tag
- **File:** `Dockerfile` (Line 1)
- **Source of Truth:** `FROM python:latest`
- **Expected Category:** `CONTAINERIZATION`
- **Expected Severity:** `HIGH`
- **Detecting Agent:** `ConfigAgent`
- **Why It Exists:** `:latest` is mutable; automatic pulls can introduce underlying glibc, system library, or Python minor version mismatches.

---

### Issue 5: Documentation / Configuration Mismatch
- **File:** `docker-compose.yml` (missing `REDIS_URL`) & `README.md`
- **Source of Truth:** `README.md` states: *"Mandatory Requirement: Production deployment requires REDIS_URL for distributed transaction caching..."*, but `docker-compose.yml` omits it.
- **Expected Category:** `DOCUMENTATION`
- **Expected Severity:** `HIGH`
- **Detecting Agent:** `RAGAgent`
- **Why It Exists:** Proves Agentic RAG retrieves repository documentation rules and compares them with actual deployment manifests.

---

### Issue 6: Missing Regression Tests for Critical Payment Logic
- **File:** `src/payment.py`
- **Source of Truth:** `tests/test_app.py` exists, but no test covers `PaymentProcessor`.
- **Expected Category:** `TEST`
- **Expected Severity:** `HIGH`
- **Detecting Agent:** `TestAgent` (classified as `INFERRED`)
- **Why It Exists:** Demonstrates the Test Agent's distinction between OBSERVED test outcomes and INFERRED missing tests for high-impact business modules.
