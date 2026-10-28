from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.database import init_db, get_db
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.flow import router as flow_router
from backend.app.api.v1.repositories import router as repositories_router
from backend.app.api.v1.analysis import router as analysis_router
from backend.app.api.v1.dashboard import router as dashboard_router
from backend.app.api.v1.runs import router as runs_router
from backend.app.api.v1.findings import router as findings_router
from backend.app.api.v1.observability import router as observability_router
from backend.app.api.v1.evaluation import router as evaluation_router

# Startup actions
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Starting %s v%s in %s environment...", settings.PROJECT_NAME, settings.VERSION, settings.APP_ENV)
    init_db()
    logger.info("Active LLM provider: %s", settings.get_active_provider())
    yield
    # Shutdown actions
    logger.info("Shutting down %s...", settings.PROJECT_NAME)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Multi-agent AI deployment-readiness intelligence platform.",
    lifespan=lifespan
)

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    settings.FRONTEND_URL,
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error processing %s: %s", request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please consult backend logs."}
    )

# Include API v1 routers
app.include_router(health_router, prefix="/api/v1", tags=["System & Health"])
app.include_router(flow_router, prefix="/api/v1/flow", tags=["CrewAI Flows"])
app.include_router(repositories_router, prefix="/api/v1/repositories", tags=["Repositories & RAG"])
app.include_router(analysis_router, prefix="/api/v1/analysis", tags=["Multi-Agent Analysis"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard & Executive Metrics"])
app.include_router(runs_router, prefix="/api/v1/runs", tags=["Runs & Findings Management"])
app.include_router(findings_router, prefix="/api/v1/findings", tags=["Findings Directory"])
app.include_router(observability_router, prefix="/api/v1", tags=["Observability & Tracing"])
app.include_router(evaluation_router, prefix="/api/v1", tags=["Benchmark Evaluation"])

# Root fallback & Health check
@app.get("/health")
def read_root_health(db: Session = Depends(get_db)):
    from backend.app.api.v1.health import get_health
    return get_health(db)


@app.get("/")
def read_root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_url": "/api/v1/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
