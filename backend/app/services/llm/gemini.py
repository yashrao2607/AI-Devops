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

class GeminiProvider(LLMProvider):
    """Google Gemini LLM Provider utilizing Google's Generative Language API."""

    def __init__(self, api_key: Optional[str], model_name: str = "gemini-2.0-flash", timeout: int = 30):
        super().__init__(model_name=model_name, timeout=timeout)
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _check_auth(self):
        if not self.api_key or self.api_key.startswith("YOUR_") or not self.api_key.strip():
            raise LLMAuthenticationError("GEMINI_API_KEY is not configured or contains placeholder.")

    def _call_api(self, payload: dict) -> dict:
        self._check_auth()
        url = f"{self.base_url}/{self.model_name}:generateContent?key={self.api_key}"
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload, headers={"Content-Type": "application/json"})
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code in (401, 403):
                    raise LLMAuthenticationError(f"Gemini authentication failed (HTTP {response.status_code}): {response.text}")
                elif response.status_code == 429:
                    raise LLMRateLimitError(f"Gemini rate limit exceeded: {response.text}")
                else:
                    raise LLMProviderError(f"Gemini API returned status {response.status_code}: {response.text}")
        except httpx.TimeoutException:
            raise LLMTimeoutError(f"Gemini request timed out after {self.timeout}s.")
        except (LLMAuthenticationError, LLMRateLimitError, LLMProviderError, LLMTimeoutError):
            raise
        except Exception as e:
            raise LLMProviderError(f"Gemini connection error: {str(e)}")

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        def _do_generate():
            contents = []
            if system_prompt:
                contents.append({"role": "user", "parts": [{"text": f"System Instruction: {system_prompt}"}]})
                contents.append({"role": "model", "parts": [{"text": "Understood."}]})
            contents.append({"role": "user", "parts": [{"text": prompt}]})

            payload = {"contents": contents}
            data = self._call_api(payload)
            
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError) as e:
                raise LLMProviderError(f"Unexpected response structure from Gemini: {data}")

        return self._execute_with_retry(_do_generate)

    def generate_structured(self, prompt: str, schema: Type[T], system_prompt: Optional[str] = None, **kwargs) -> T:
        json_schema = schema.model_json_schema()
        instructions = (
            f"You MUST return a valid JSON object strictly matching this JSON Schema:\n"
            f"{json.dumps(json_schema)}\n"
            f"Do not include markdown codeblocks or explanations outside the JSON."
        )
        full_system = f"{system_prompt}\n{instructions}" if system_prompt else instructions
        
        raw_output = self.generate(prompt=prompt, system_prompt=full_system, **kwargs)
        
        # Clean json output if enclosed in code blocks
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
            logger.error("Failed to parse structured output from Gemini: %s\nRaw: %s", str(e), raw_output)
            raise LLMProviderError(f"Gemini failed to return valid schema: {str(e)}")
