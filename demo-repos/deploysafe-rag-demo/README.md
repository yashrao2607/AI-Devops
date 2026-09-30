# Demo Application — Cloud Microservice

This is a demonstration microservice repository used to validate DeploySafe's repository ingestion, AST analysis, configuration discovery, and RAG knowledge retrieval.

---

## 1. Deployment Instructions

To deploy this microservice in staging or production:
```bash
docker compose up -d --build
```
The application will listen on port `8080` by default.
Verify deployment health by querying:
`GET http://localhost:8080/health`

Production deployments require mounting a persistent PostgreSQL volume and setting `APP_ENV=production`.

---

## 2. Environment Variables Documentation

The application reads configuration from `.env` or system environment variables:
- `DATABASE_URL`: Connection string for PostgreSQL (e.g. `postgresql://user:pass@localhost:5432/appdb`). Default: `sqlite:///./app.db`.
- `PORT`: HTTP port to bind the server (default: `8080`).
- `JWT_SECRET`: Secret key used for signing session tokens. Must be at least 32 characters in production.
- `APP_ENV`: Deployment tier (`development`, `staging`, `production`).

---

## 3. Testing Instructions

Run the automated test suite using pytest:
```bash
pytest tests/ -v --cov=src
```
Before running tests, ensure local dependencies are installed via `pip install -r requirements.txt`.
Unit tests do not require an active database connection as database operations are mocked.
