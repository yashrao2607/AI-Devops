import time
from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar, Any
from pydantic import BaseModel
from backend.app.core.logging import logger

T = TypeVar("T", bound=BaseModel)

class LLMProviderError(Exception):
    """Base exception for all LLM provider failures."""
    pass

class LLMRateLimitError(LLMProviderError):
    """Raised when provider returns HTTP 429 or rate limits."""
    pass

class LLMAuthenticationError(LLMProviderError):
    """Raised when API key is missing or invalid."""
    pass

class LLMTimeoutError(LLMProviderError):
    """Raised when provider call exceeds configured timeout."""
    pass

class LLMProvider(ABC):
    """Abstract Base Class for LLM providers."""

    def __init__(self, model_name: str, timeout: int = 30, max_retries: int = 2):
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generates plain text response from the model."""
        pass

    @abstractmethod
    def generate_structured(self, prompt: str, schema: Type[T], system_prompt: Optional[str] = None, **kwargs) -> T:
        """Generates structured response validated against a Pydantic schema."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the provider name identifier."""
        pass

    def _execute_with_retry(self, func, *args, **kwargs) -> Any:
        """Executes a function with capped exponential backoff."""
        attempt = 0
        last_error = None
        while attempt <= self.max_retries:
            try:
                return func(*args, **kwargs)
            except LLMAuthenticationError:
                # Do not retry auth errors
                raise
            except LLMRateLimitError as e:
                attempt += 1
                if attempt > self.max_retries:
                    raise
                backoff = min(2 ** attempt, 8)
                logger.warning("[%s] Rate limit hit. Backing off for %ds (attempt %d/%d)", 
                               self.provider_name, backoff, attempt, self.max_retries)
                time.sleep(backoff)
            except Exception as e:
                attempt += 1
                last_error = e
                if attempt > self.max_retries:
                    break
                backoff = min(2 ** attempt, 4)
                logger.warning("[%s] Request failed: %s. Retrying in %ds...", self.provider_name, str(e), backoff)
                time.sleep(backoff)
        raise LLMProviderError(f"[{self.provider_name}] Failed after {self.max_retries} retries: {str(last_error)}")
