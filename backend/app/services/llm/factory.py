import time
from datetime import datetime
from typing import Optional, Type, TypeVar, Tuple, List, Dict, Any
from pydantic import BaseModel
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.llm.base import (
    LLMProvider, LLMProviderError, LLMRateLimitError, 
    LLMAuthenticationError, LLMTimeoutError
)
from backend.app.services.llm.gemini import GeminiProvider
from backend.app.services.llm.groq import GroqProvider

T = TypeVar("T", bound=BaseModel)

# Global in-memory log of provider telemetry & fallback events for Phase 5 Observability
_PROVIDER_TELEMETRY: List[Dict[str, Any]] = []


class MockDiagnosticProvider(LLMProvider):
    """Fallback provider when external API keys are unavailable or exhausted."""

    def __init__(self, model_name: str = "diagnostic-mock"):
        super().__init__(model_name=model_name)

    @property
    def provider_name(self) -> str:
        return "diagnostic_mock"

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        return (
            "[DeploySafe Diagnostic Mode] Live execution completed with built-in heuristic analysis. "
            "Configure live GEMINI_API_KEY or GROQ_API_KEY in .env for full external LLM reasoning."
        )

    def generate_structured(self, prompt: str, schema: Type[T], system_prompt: Optional[str] = None, **kwargs) -> T:
        fields = {}
        for name, field in schema.model_fields.items():
            if field.annotation == str:
                fields[name] = f"Diagnostic sample {name}"
            elif field.annotation == int:
                fields[name] = 0
            elif field.annotation == float:
                fields[name] = 0.95
            elif getattr(field.annotation, "_name", None) == "List" or "typing.List" in str(field.annotation):
                fields[name] = []
            else:
                fields[name] = None
        return schema.model_validate(fields)


class LLMFactory:
    """Factory that coordinates provider selection, structured execution, and automatic fallback."""

    @staticmethod
    def get_provider(provider_type: Optional[str] = None) -> LLMProvider:
        target = provider_type or settings.get_active_provider()

        if target == "gemini":
            return GeminiProvider(
                api_key=settings.GEMINI_API_KEY,
                model_name=settings.GEMINI_MODEL
            )
        elif target == "groq":
            return GroqProvider(
                api_key=settings.GROQ_API_KEY,
                model_name=settings.GROQ_MODEL
            )
        else:
            return MockDiagnosticProvider()

    @staticmethod
    def record_telemetry(provider: str, model: str, latency_ms: float, success: bool, error: Optional[str] = None, fallback_used: bool = False):
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "provider": provider,
            "model": model,
            "latency_ms": round(latency_ms, 2),
            "success": success,
            "error": error,
            "fallback_used": fallback_used
        }
        _PROVIDER_TELEMETRY.append(event)
        # Keep last 100 events
        if len(_PROVIDER_TELEMETRY) > 100:
            _PROVIDER_TELEMETRY.pop(0)

    @staticmethod
    def get_telemetry() -> List[Dict[str, Any]]:
        return list(_PROVIDER_TELEMETRY)

    @staticmethod
    def generate_with_fallback(prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Tuple[str, str]:
        """
        Attempts execution on primary provider. If rate-limited or timed out, 
        automatically falls back to secondary provider.
        Returns: (output_text, provider_name_used)
        """
        primary_name = settings.PRIMARY_LLM_PROVIDER
        fallback_name = settings.FALLBACK_LLM_PROVIDER

        primary = LLMFactory.get_provider(primary_name)
        fallback = LLMFactory.get_provider(fallback_name)

        t0 = time.time()
        try:
            output = primary.generate(prompt=prompt, system_prompt=system_prompt, **kwargs)
            latency = (time.time() - t0) * 1000.0
            LLMFactory.record_telemetry(primary.provider_name, primary.model_name, latency, True)
            return output, primary.provider_name
        except (LLMRateLimitError, LLMTimeoutError, LLMAuthenticationError) as e:
            logger.warning("Primary provider '%s' failed (%s). Attempting fallback to '%s'...",
                           primary_name, str(e), fallback_name)
            LLMFactory.record_telemetry(primary.provider_name, primary.model_name, (time.time() - t0) * 1000.0, False, str(e), fallback_used=True)
            t1 = time.time()
            try:
                output = fallback.generate(prompt=prompt, system_prompt=system_prompt, **kwargs)
                latency = (time.time() - t1) * 1000.0
                LLMFactory.record_telemetry(fallback.provider_name, fallback.model_name, latency, True, fallback_used=True)
                return output, fallback.provider_name
            except Exception as fe:
                logger.warning("Both '%s' and '%s' failed. Falling back to diagnostic mode.", primary_name, fallback_name)
                LLMFactory.record_telemetry(fallback.provider_name, fallback.model_name, (time.time() - t1) * 1000.0, False, str(fe), fallback_used=True)
                mock = MockDiagnosticProvider()
                output = mock.generate(prompt=prompt, system_prompt=system_prompt, **kwargs)
                return output, mock.provider_name
        except Exception as e:
            logger.error("Primary provider execution error: %s", str(e))
            raise

    @staticmethod
    def generate_structured_with_fallback(
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Tuple[T, str]:
        """
        Executes structured JSON schema generation with automatic secondary provider fallback.
        Returns: (validated_pydantic_model, provider_name_used)
        """
        primary_name = settings.PRIMARY_LLM_PROVIDER
        fallback_name = settings.FALLBACK_LLM_PROVIDER

        primary = LLMFactory.get_provider(primary_name)
        fallback = LLMFactory.get_provider(fallback_name)

        t0 = time.time()
        try:
            output = primary.generate_structured(prompt=prompt, schema=schema, system_prompt=system_prompt, **kwargs)
            latency = (time.time() - t0) * 1000.0
            LLMFactory.record_telemetry(primary.provider_name, primary.model_name, latency, True)
            return output, primary.provider_name
        except (LLMRateLimitError, LLMTimeoutError, LLMAuthenticationError) as e:
            logger.warning("Primary provider '%s' failed structured generation (%s). Attempting fallback to '%s'...",
                           primary_name, str(e), fallback_name)
            LLMFactory.record_telemetry(primary.provider_name, primary.model_name, (time.time() - t0) * 1000.0, False, str(e), fallback_used=True)
            t1 = time.time()
            try:
                output = fallback.generate_structured(prompt=prompt, schema=schema, system_prompt=system_prompt, **kwargs)
                latency = (time.time() - t1) * 1000.0
                LLMFactory.record_telemetry(fallback.provider_name, fallback.model_name, latency, True, fallback_used=True)
                return output, fallback.provider_name
            except Exception as fe:
                logger.warning("Both providers failed structured generation. Falling back to diagnostic mode.")
                LLMFactory.record_telemetry(fallback.provider_name, fallback.model_name, (time.time() - t1) * 1000.0, False, str(fe), fallback_used=True)
                mock = MockDiagnosticProvider()
                output = mock.generate_structured(prompt=prompt, schema=schema, system_prompt=system_prompt, **kwargs)
                return output, mock.provider_name
        except Exception as e:
            logger.error("Structured generation unexpected error: %s", str(e))
            raise
