# DeploySafe Typed Tool Layer (Phase 3)

## 1. Overview
In DeploySafe, agents never execute arbitrary or unbounded commands. All interactions with the repository, filesystem, vector store, test runners, and static scanners are mediated by typed Python tool classes with strict permission boundaries, timeouts, output caps, and path sandboxing.

---

## 2. Safe Command Executor (`SafeCommandExecutor`)
**Location:** `backend/app/services/tools/safe_executor.py`

### Security Guarantees:
- **Strict Binary Allowlist:** Only approved executables may run:
  - `git`
  - `pytest`
  - `python`
  - `npm`
  - `bandit`
  - `gitleaks`
  - `osv-scanner`
  Any attempt to invoke unlisted binaries (e.g. `bash`, `curl`, `powershell`, `rm`) raises `PermissionError` immediately.
- **Path Sandboxing:** All commands execute strictly within the designated repository root directory.
- **Subprocess Safety:** `shell=False` is enforced. Commands are passed as structured argument lists to prevent shell injection.
- **Resource Constraints:**
  - Configurable timeout (default: 30 seconds).
  - Output truncation capped at 100 KB to prevent memory exhaustion from verbose outputs.
- **Execution Telemetry:** Returns `SafeExecutionResult` containing return code, duration, captured stdout, captured stderr, and timeout flags.

---

## 3. Repository File Tools (`RepositoryTools`)
**Location:** `backend/app/services/tools/repo_tools.py`

### Implemented Methods:
1. `get_file_content(context, file_path, start_line, end_line)`:
   - Line-accurate slicing of repository files (1-indexed).
   - Defends against Directory Traversal attacks (`../`) by validating path resolution within `context.root_path`.
2. `get_git_diff(context)`:
   - Executes safe `git diff` inside the repository to isolate changed files and line modifications.
3. `get_dependency_manifests(context)`:
   - Discovers and categorizes package manifests (`requirements.txt`, `package.json`, `pyproject.toml`).
4. `get_test_files(context)`:
   - Identifies automated test files across `tests/`, `spec/`, or pattern matching `test_*.py`.

---

## 4. Semantic RAG Tools (`RAGTools`)
**Location:** `backend/app/services/tools/rag_tools.py`

### Implemented Methods:
1. `search_repository_context(repository_id, query, top_k, category)`:
   - Executes semantic vector queries over Chroma collections indexed during Phase 2.
   - Returns structured `RAGQueryItem` citations with relevance scores, line ranges, and source content.
   - Enforces repository-level collection isolation.

---

## 5. Security Scanner Tools (`SecurityTools`)
**Location:** `backend/app/services/tools/security_tools.py`

### Implemented Methods:
1. `run_security_scan(context)`:
   - Orchestrates deterministic static analysis combining Bandit (if installed) and AST / regex credential detectors.
   - Scans for high-entropy secrets, private keys, database connection strings, and authorization tokens.
   - **Secret Masking:** Automatically replaces sensitive tokens in snippets with `***REDACTED_SECRET***`.
2. `detect_secrets(text)`:
   - Regex pattern matcher identifying URI credentials (`postgres://user:pass@host`), JWT headers, and private key headers.

---

## 6. Safe Test Runner Tools (`TestTools`)
**Location:** `backend/app/services/tools/test_tools.py`

### Implemented Methods:
1. `run_tests_safe(context, test_paths, timeout_seconds)`:
   - Invokes `pytest` within the repository under sandboxed constraints.
   - Parses output to extract total tests, passed, failed, and error counts.
   - Captures failure snippets for test failure findings.
