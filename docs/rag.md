# DeploySafe — RAG & Repository Analysis Architecture

## 1. What RAG Means in DeploySafe
In DeploySafe, Retrieval-Augmented Generation (RAG) is the foundational intelligence mechanism that enables autonomous risk and readiness agents to inspect, understand, and verify software repositories without hallucinations.

Instead of passing entire codebases into model context windows or generating speculative advice, DeploySafe extracts verifiable repository evidence:
- **Traceable Attribution:** Every retrieved evidence chunk references its exact repository origin, file path, starting line, ending line, and AST/structural category.
- **Zero Hallucination Guarantee:** DeploySafe enforces relevance thresholding (`FOUND`, `LOW_RELEVANCE`, `NOT_FOUND`). When evidence does not exist in the repository, DeploySafe explicitly signals `NOT_FOUND` rather than manufacturing speculative answers.
- **Isolation:** Repositories are strictly segregated via Chroma vector collections and query filter predicates (`where={"repository_id": ...}`), guaranteeing zero cross-repository data contamination.

---

## 2. Ingestion Pipeline
DeploySafe supports three normalized ingestion vectors:
1. **Local Filesystem:** Ingests local directory snapshots with path normalization, existence checks, directory verification, and symlink security.
2. **Remote GitHub:** Safely clones public and token-authenticated repositories using shallow clones (`--depth 1`), validating URLs and protecting credentials.
3. **ZIP Archive:** Uploads and extracts `.zip` packages within temporary sandboxes, enforcing strict Zip-Slip path traversal defense, file count caps (2,000 files), and extraction volume quotas (200MB).

All three vectors produce a uniform `RepositorySnapshot` containing:
- `repository_id`
- `repository_name`
- `source_type` (`local` | `github` | `zip`)
- `root_path`
- `branch`
- `commit_sha`
- `file_count`
- `total_size_bytes`

---

## 3. File Discovery, Filtering & Secret Redaction
The discovery engine recursively scans the ingested root and categorizes files into 8 structural domains:
- `SOURCE_CODE`: Python, TypeScript, JavaScript, Go, Rust, Java, C/C++, PHP, Ruby
- `TEST`: Test suites, unit tests, integration test scripts (`test_*.py`, `*.spec.ts`, etc.)
- `CONFIG`: Configuration manifests (YAML, JSON, TOML, XML, `.env.example`)
- `DOCUMENTATION`: Markdown (`.md`), guides, deployment architecture docs
- `DOCKER`: `Dockerfile`, `docker-compose.yml`, container definitions
- `CI_CD`: Workflow definitions (`.github/workflows/*.yml`, CI pipeline specs)
- `SCRIPT`: Shell scripts (`.sh`, `.bash`, `.bat`, `.ps1`)
- `OTHER`: Unclassified project assets

### Ignore Policy
The following directories and artifacts are systematically ignored:
- VCS: `.git/`, `.svn/`, `.hg/`
- Build/Package Artifacts: `node_modules/`, `dist/`, `build/`, `.venv/`, `venv/`, `target/`
- Cache/Locks: `__pycache__/`, `.pytest_cache/`, `*.pyc`, `package-lock.json`, `poetry.lock`
- Binaries & Media: Images, videos, archives, compiled binaries (`.exe`, `.so`, `.dylib`)

### Secret-Aware Ingestion
DeploySafe inspects file contents prior to chunking and embeddings. Regular expressions detect API keys, private keys, passwords, and authorization tokens, automatically replacing them with `***REDACTED_SECRET***` in both embeddings and stored vector snippets.

---

## 4. Intelligent Semantic Chunking
DeploySafe departs from naive character/token windowing in favor of repository-aware semantic chunking:
- **Markdown:** Split along heading hierarchies (`#`, `##`, `###`), preserving complete conceptual sections.
- **Code (Python / JS / TS):** Split along class definitions, functions, and top-level module blocks.
- **Docker & CI/CD:** Split along instruction blocks (`FROM`, `RUN`, `COPY`, `CMD`) and YAML workflow steps.
- **Line-Number Tracking:** Every chunk computes deterministic starting and ending line numbers (`line_start`, `line_end`) directly against the source file content.
- **Deterministic IDs:** Chunk IDs follow the format `chk_{md5(repo:path:start:end)[:16]}`.

---

## 5. Embeddings Layer
DeploySafe provides an extensible `EmbeddingProvider` abstraction:
- **Primary:** `GeminiEmbeddingProvider` using Google's `text-embedding-004` (768 dimensions), utilizing batch endpoints and exponential backoff retry.
- **Fallback / Local:** `LocalEmbeddingProvider` using normalized 384-dimensional deterministic feature projections with alphanumeric word tokens, sub-word prefixes, character n-grams, and stop-word filtering. Guarantees 100% test reliability and zero dependency on remote networks or GPU download delays.

---

## 6. Chroma Vector Store & Repository Isolation
Chroma is used for persistent local vector storage:
- **Storage Path:** Configured via `CHROMA_PATH` in `.env` (default `./chroma_db`).
- **Testing Mode:** Supports `:memory:` ephemeral mode (`chromadb.EphemeralClient()`) for fast, lock-free unit and integration testing on Windows.
- **Repository Isolation:** Every collection is namespaced (`{prefix}_{repo_id}`), and all queries mandate a `where={"repository_id": repo_id}` clause. Chunks from Repository A can never be retrieved when querying Repository B.

---

## 7. Retrieval Service (`RepositoryRetriever`)
The retriever handles natural-language questions and returns structured repository evidence:
- **Input:** `query: str`, `repository_id: str`, `top_k: int = 5`, `filters: Optional[dict] = None`
- **Output:** `SearchResponse` containing:
  - `status`: `"FOUND"`, `"LOW_RELEVANCE"`, or `"NOT_FOUND"`
  - `results`: List of `SearchResult` objects (`chunk_id`, `relevance_score`, `file_path`, `line_start`, `line_end`, `category`, `language`, `content`, `commit_sha`)
  - `results_count`: Number of matching evidence snippets
  - `message`: Diagnostic and explanation status

---

## 8. Limitations & Future Work (Phases 3+)
- Current chunking uses heuristic syntactic boundaries (regex/heading-based). Phase 3 will introduce tree-sitter AST parsing for deeper semantic graph relationships.
- Phase 2 focuses strictly on repository ingestion and evidence retrieval; autonomous multi-agent evaluation and the final risk score engine will be built in Phase 3.
