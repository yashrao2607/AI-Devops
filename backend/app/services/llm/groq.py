import json
import httpx
from typing import Optional, Type, TypeVar
from pydantic import BaseModel
from backend.app.services.llm.base import (
    LLMProvider, LLMProviderError, LLMRateLimitError, 
    LLMAuthenticationError, LLMTimeoutError
)
from backend.app.core.logging import logger

T = TypeVar("T", bound=BaseModel)

class GroqProvider(LLMProvider):
    """Groq Cloud LLM Provider with OpenAI-compatible endpoint."""

    def __init__(self, api_key: Optional[str], model_name: str = "openai/gpt-oss-120b", timeout: int = 30):
        super().__init__(model_name=model_name, timeout=timeout)
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    @property
    def provider_name(self) -> str:
        return "groq"

    def _check_auth(self):
        if not self.api_key or self.api_key.startswith("YOUR_") or not self.api_key.strip():
            raise LLMAuthenticationError("GROQ_API_KEY is not configured or contains placeholder.")

    def _call_api(self, payload: dict) -> dict:
        self._check_auth()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.base_url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    return response.json()
                elif (response.status_code == 404 and "model_not_found" in response.text) or response.status_code == 429:
                    # Model not available or rate limited on this account/tier, fallback to working models
                    fallback_models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
                    for alt_model in fallback_models:
                        if alt_model != payload.get("model"):
                            logger.info("[groq] Model '%s' status %d. Trying alternative '%s'...", payload.get("model"), response.status_code, alt_model)
                            alt_payload = dict(payload)
                            alt_payload["model"] = alt_model
                            alt_res = client.post(self.base_url, json=alt_payload, headers=headers)
                            if alt_res.status_code == 200:
                                self.model_name = alt_model
                                return alt_res.json()
                    if response.status_code == 429:
                        raise LLMRateLimitError(f"Groq rate limit exceeded across models: {response.text}")
                    raise LLMProviderError(f"Groq API returned status 404: {response.text}")
                elif response.status_code in (401, 403):
                    raise LLMAuthenticationError(f"Groq authentication failed (HTTP {response.status_code}): {response.text}")
                else:
                    raise LLMProviderError(f"Groq API returned status {response.status_code}: {response.text}")
        except httpx.TimeoutException:
            raise LLMTimeoutError(f"Groq request timed out after {self.timeout}s.")
        except (LLMAuthenticationError, LLMRateLimitError, LLMProviderError, LLMTimeoutError):
            raise
        except Exception as e:
            raise LLMProviderError(f"Groq connection error: {str(e)}")

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        def _do_generate():
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.2
            }
            data = self._call_api(payload)
            
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError) as e:
                raise LLMProviderError(f"Unexpected response structure from Groq: {data}")

        return self._execute_with_retry(_do_generate)

    def generate_structured(self, prompt: str, schema: Type[T], system_prompt: Optional[str] = None, **kwargs) -> T:
        json_schema = schema.model_json_schema()
        instructions = (
            f"You MUST return a valid JSON object strictly adhering to this schema:\n"
            f"{json.dumps(json_schema)}\n"
            f"Do not write explanations, markdown fences, or preamble."
        )
        full_system = f"{system_prompt}\n{instructions}" if system_prompt else instructions
        
        raw_output = self.generate(prompt=prompt, system_prompt=full_system, **kwargs)
        
        clean_json = raw_output.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        if clean_json.startswith("```"):
            clean_json = clean_json[3:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
        clean_json = clean_json.strip()

        try:
            return schema.model_validate_json(clean_json)
        except Exception as e:
            logger.error("Failed to parse structured output from Groq: %s\nRaw: %s", str(e), raw_output)
            raise LLMProviderError(f"Groq failed to return valid schema: {str(e)}")
