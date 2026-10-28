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
        github_configured=settings.has_github,
        database_status=db_status,
        timestamp=datetime.utcnow()
    )

@router.post("/settings/github-token")
def set_github_token(payload: dict):
    """Sets or updates the GitHub access token at runtime and persists to .env."""
    token = (payload.get("token") or "").strip()
    settings.GITHUB_TOKEN = token if token else None
    
    # Try updating .env file if it exists
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            new_lines = []
            found = False
            for line in lines:
                if line.startswith("GITHUB_TOKEN="):
                    new_lines.append(f"GITHUB_TOKEN={token}\n")
                    found = True
                else:
                    new_lines.append(line)
            if not found:
                new_lines.append(f"GITHUB_TOKEN={token}\n")
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        except Exception:
            pass

    return {
        "success": True,
        "github_configured": settings.has_github,
        "message": "GitHub access token updated successfully." if settings.has_github else "GitHub access token cleared."
    }

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
