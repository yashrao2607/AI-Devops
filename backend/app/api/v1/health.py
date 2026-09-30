import time
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.schemas import HealthResponse, LLMDiagnosticRequest, LLMDiagnosticResponse
from backend.app.services.llm.factory import LLMFactory

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)):
    """Health check endpoint validating API, Database, and LLM configuration."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.APP_ENV,
        active_llm_provider=settings.get_active_provider(),
        gemini_configured=settings.has_gemini,
        groq_configured=settings.has_groq,
        database_status=db_status,
        timestamp=datetime.utcnow()
    )

@router.post("/diagnostic/llm", response_model=LLMDiagnosticResponse)
def test_llm_diagnostic(payload: LLMDiagnosticRequest):
    """Executes a diagnostic LLM call to verify provider responsiveness and measure latency."""
    start_time = time.time()
    try:
        content, provider_used = LLMFactory.generate_with_fallback(
            prompt=payload.prompt,
            system_prompt="You are the DeploySafe AI Diagnostic Assistant. Respond briefly and technically."
        )
        latency_ms = round((time.time() - start_time) * 1000, 2)
        return LLMDiagnosticResponse(
            provider_used=provider_used,
            model_used=settings.GEMINI_MODEL if provider_used == "gemini" else settings.GROQ_MODEL,
            success=True,
            content=content,
            latency_ms=latency_ms,
            error=None
        )
    except Exception as e:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        return LLMDiagnosticResponse(
            provider_used=payload.provider or settings.PRIMARY_LLM_PROVIDER,
            model_used="unknown",
            success=False,
            content="",
            latency_ms=latency_ms,
            error=str(e)
        )
