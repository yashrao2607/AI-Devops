# DeploySafe — Environment Variable Setup Guide

This guide explains every environment variable used by **DeploySafe**, why it is needed, how to get your own API keys, and what happens if any key is missing.

---

## Quick Summary

| Environment Variable | Status in Phase 1 | Where to Obtain |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Optional for Phase 1 (mock/diagnostic mode available) | [Google AI Studio](https://aistudio.google.com/) |
| `GROQ_API_KEY` | Optional fallback | [Groq Console](https://console.groq.com/keys) |
| `GITHUB_TOKEN` | Optional (used in Phase 2 & 5) | [GitHub Token Settings](https://github.com/settings/tokens) |
| `PRIMARY_LLM_PROVIDER` | Pre-configured (`gemini`) | In `.env` |
| `FALLBACK_LLM_PROVIDER`| Pre-configured (`groq`) | In `.env` |
| `DATABASE_URL` | Pre-configured (`sqlite:///./deploysafe.db`) | Automatic SQLite local file |
| `CHROMA_PATH` | Pre-configured (`./chroma_db`) | Local directory |

---

## Detailed Variable Guides

### 1. `GEMINI_API_KEY`

1. **Variable Name:** `GEMINI_API_KEY`
2. **Why DeploySafe Needs It:**
   DeploySafe uses Google Gemini (such as `gemini-2.0-flash` or `gemini-1.5-flash`) as its primary LLM to analyze code snippets, reason over configuration files, summarize deployment risks, and generate structured readiness assessments.
3. **Requirement:**
   Optional for initial Phase 1 foundation checks (the system runs in safe diagnostic/mock mode without crashing). Required when performing live AI queries.
4. **Where to Get It:**
   Google AI Studio: [https://aistudio.google.com/](https://aistudio.google.com/)
5. **Basic Steps to Obtain:**
   - Step 1: Open [https://aistudio.google.com/](https://aistudio.google.com/) in your browser.
   - Step 2: Sign in with your Google account.
   - Step 3: Click **Get API key** in the left menu.
   - Step 4: Click **Create API key in new project** (or select an existing Google Cloud project).
   - Step 5: Copy the generated key.
6. **Where to Paste It:**
   Open the `.env` file in the project root and paste it:
   ```env
   GEMINI_API_KEY=AIzaSyD...your_actual_key_here...
   ```
7. **Security Warning:**
   Never commit `.env` or share your API key publicly. Keep it strictly private on your machine.
8. **What Happens If It Is Missing:**
   DeploySafe will detect the missing key at startup, log a friendly warning, and fallback to the secondary provider (`groq`) if configured, or run in diagnostic mode. The backend server will not crash.

---

### 2. `GROQ_API_KEY`

1. **Variable Name:** `GROQ_API_KEY`
2. **Why DeploySafe Needs It:**
   DeploySafe uses Groq Cloud as an ultra-fast secondary/fallback LLM provider. If Gemini experiences a rate limit (HTTP 429) or outage, DeploySafe automatically falls back to Groq.
3. **Requirement:**
   Optional. Useful as an automatic failover.
4. **Where to Get It:**
   Groq Cloud Console: [https://console.groq.com/keys](https://console.groq.com/keys)
5. **Basic Steps to Obtain:**
   - Step 1: Open [https://console.groq.com/](https://console.groq.com/) and create a free account or log in.
   - Step 2: Navigate to **API Keys** in the dashboard.
   - Step 3: Click **Create API Key**.
   - Step 4: Name it (e.g. `deploysafe-dev`) and copy the secret key.
6. **Where to Paste It:**
   In `.env`:
   ```env
   GROQ_API_KEY=gsk_...your_actual_key_here...
   ```
7. **Security Warning:**
   Groq API keys give access to inference compute. Never paste them into client-side code or public chats.
8. **What Happens If It Is Missing:**
   DeploySafe logs that the fallback provider is unavailable. If the primary provider also fails, DeploySafe reports a clean user-facing error message instead of crashing.

---

### 3. `GITHUB_TOKEN`

1. **Variable Name:** `GITHUB_TOKEN`
2. **Why DeploySafe Needs It:**
   Used in Phase 2 and Phase 5 to clone or read remote repositories, inspect Pull Request diffs, and post comments or commit checks back to GitHub Actions.
3. **Requirement:**
   Not required in Phase 1. Recommended in Phase 2+ for private GitHub repositories.
4. **Where to Get It:**
   GitHub Personal Access Tokens: [https://github.com/settings/tokens](https://github.com/settings/tokens)
5. **Basic Steps to Obtain:**
   - Step 1: Go to GitHub -> Settings -> Developer settings -> Personal access tokens -> Fine-grained tokens (or Tokens classic).
   - Step 2: Click **Generate new token**.
   - Step 3: Select `repo` read/write permissions for repositories you wish to scan.
   - Step 4: Copy the token immediately.
6. **Where to Paste It:**
   In `.env`:
   ```env
   GITHUB_TOKEN=ghp_...your_actual_token_here...
   ```
7. **Security Warning:**
   Tokens grant repository access. Ensure this token never leaks into client-side bundles or public repositories.
8. **What Happens If It Is Missing:**
   In Phase 1, nothing. In Phase 2+, DeploySafe can still analyze local repositories and public GitHub repositories without a token.

---

### 4. `PRIMARY_LLM_PROVIDER` & `FALLBACK_LLM_PROVIDER`

1. **Variable Names:** `PRIMARY_LLM_PROVIDER`, `FALLBACK_LLM_PROVIDER`
2. **Why DeploySafe Needs It:**
   Determines the order of priority for AI reasoning models.
3. **Allowed Values:** `gemini`, `groq`
4. **Default Setting:**
   ```env
   PRIMARY_LLM_PROVIDER=gemini
   FALLBACK_LLM_PROVIDER=groq
   ```
5. **What Happens If Missing or Misconfigured:**
   DeploySafe defaults to `gemini` with `groq` as fallback and logs a validation warning if an invalid provider name is passed.

---

### 5. `DATABASE_URL`

1. **Variable Name:** `DATABASE_URL`
2. **Why DeploySafe Needs It:**
   Stores repository run history, findings, agent trace logs, and deployment reports.
3. **Default Value:**
   ```env
   DATABASE_URL=sqlite:///./deploysafe.db
   ```
4. **What Happens If Missing:**
   DeploySafe automatically defaults to a local SQLite database file named `deploysafe.db` inside the project directory. Zero external database configuration required.

---

### 6. `CHROMA_PATH`
 
 1. **Variable Name:** `CHROMA_PATH`
 2. **Why DeploySafe Needs It:**
    Specifies the local directory where Chroma vector embeddings will be persisted (for Phase 2 RAG).
 3. **Default Value:**
    ```env
    CHROMA_PATH=./chroma_db
    ```
 4. **What Happens If Missing:**
    Chroma will initialize locally in `./chroma_db` by default.

---

### 7. Phase 2 RAG & Ingestion Limits

| Variable | Purpose | Default | Details |
| :--- | :--- | :--- | :--- |
| `EMBEDDING_PROVIDER` | Chooses embedding engine (`gemini` or `local`) | `gemini` | When `gemini`, uses `text-embedding-004`. If key missing, safely falls back to local. |
| `CHROMA_COLLECTION_PREFIX` | Namespaces repository vector collections | `deploysafe_repo` | Guarantees multi-repo isolation |
| `MAX_FILE_SIZE_MB` | Maximum single-file indexable size limit | `10` | Files exceeding this limit are skipped with clear logging |
| `MAX_REPOSITORY_SIZE_MB`| Maximum uncompressed repository volume | `200` | Defends against storage exhaustion attacks |
| `MAX_FILE_COUNT` | Maximum files discovered per repository | `2000` | Prevents runaway iteration |
| `TOP_K` | Default evidence chunks returned per search | `5` | Tunable retrieval density |

---

## Testing Your Configuration

You can verify that your environment variables and LLM providers are working at any time by running:

```powershell
python backend/tests/test_config.py
```
or by starting the backend and opening:
`http://localhost:8000/api/v1/health`
