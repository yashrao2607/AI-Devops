from typing import Optional, Type, TypeVar
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

class MockDiagnosticProvider(LLMProvider):
    """Fallback provider when no external API keys are configured (Phase 1 diagnostic mode)."""

    def __init__(self, model_name: str = "diagnostic-mock"):
        super().__init__(model_name=model_name)

    @property
    def provider_name(self) -> str:
        return "diagnostic_mock"

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        return (
            "[DeploySafe Diagnostic Mode] System is running without external API keys. "
            "Configure GEMINI_API_KEY or GROQ_API_KEY in .env to enable live LLM reasoning."
        )

    def generate_structured(self, prompt: str, schema: Type[T], system_prompt: Optional[str] = None, **kwargs) -> T:
        # Returns default schema fields if possible
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
        return schema.model_validate(fields)

class LLMFactory:
    """Factory that coordinates provider selection, execution, and automatic fallback."""

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
    def generate_with_fallback(prompt: str, system_prompt: Optional[str] = None, **kwargs) -> tuple[str, str]:
        """
        Attempts execution on primary provider. If rate-limited or failed, 
        automatically falls back to secondary provider.
        Returns: (output_text, provider_name_used)
        """
        primary_name = settings.PRIMARY_LLM_PROVIDER
        fallback_name = settings.FALLBACK_LLM_PROVIDER

        primary = LLMFactory.get_provider(primary_name)
        fallback = LLMFactory.get_provider(fallback_name)

        try:
            output = primary.generate(prompt=prompt, system_prompt=system_prompt, **kwargs)
            return output, primary.provider_name
        except (LLMRateLimitError, LLMTimeoutError, LLMAuthenticationError) as e:
            logger.warning("Primary provider '%s' failed (%s). Attempting fallback to '%s'...",
                           primary_name, str(e), fallback_name)
            try:
                output = fallback.generate(prompt=prompt, system_prompt=system_prompt, **kwargs)
                return output, fallback.provider_name
            except Exception as fe:
                logger.warning("Both '%s' and '%s' failed. Falling back to diagnostic mode.", primary_name, fallback_name)
                mock = MockDiagnosticProvider()
                output = mock.generate(prompt=prompt, system_prompt=system_prompt, **kwargs)
                return output, mock.provider_name
        except Exception as e:
            logger.error("Primary provider execution error: %s", str(e))
            raise
