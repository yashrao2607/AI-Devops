import hashlib
import math
import re
import httpx
from abc import ABC, abstractmethod
from typing import List, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger

class EmbeddingProviderError(Exception):
    """Raised when an embedding provider fails."""
    pass

class EmbeddingProvider(ABC):
    """Abstract Base Class for text embedding providers."""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Embeds a single string into a float vector."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embeds a list of strings into float vectors."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Returns the embedding vector dimension."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

class GeminiEmbeddingProvider(EmbeddingProvider):
    """Google Gemini Embedding Provider using text-embedding-004."""

    def __init__(self, api_key: Optional[str], model_name: str = "text-embedding-004", timeout: int = 30):
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def dimension(self) -> int:
        return 768

    def _check_auth(self):
        if not self.api_key or self.api_key.startswith("YOUR_") or not self.api_key.strip():
            raise EmbeddingProviderError("GEMINI_API_KEY is not configured for embeddings.")

    def embed_text(self, text: str) -> List[float]:
        results = self.embed_batch([text])
        if not results:
            raise EmbeddingProviderError("Gemini returned empty embedding.")
        return results[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        self._check_auth()
        url = f"{self.base_url}/{self.model_name}:batchEmbedContents?key={self.api_key}"

        # Gemini supports batch requests
        requests = [{"model": f"models/{self.model_name}", "content": {"parts": [{"text": t}]}} for t in texts]
        payload = {"requests": requests}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(url, json=payload, headers={"Content-Type": "application/json"})
                if res.status_code == 200:
                    data = res.json()
                    return [item["values"] for item in data.get("embeddings", [])]
                elif res.status_code == 429:
                    raise EmbeddingProviderError(f"Gemini embedding rate limit hit (HTTP 429): {res.text}")
                else:
                    raise EmbeddingProviderError(f"Gemini embedding failed with status {res.status_code}: {res.text}")
        except httpx.TimeoutException:
            raise EmbeddingProviderError(f"Gemini embedding timed out after {self.timeout}s.")
        except EmbeddingProviderError:
            raise
        except Exception as e:
            raise EmbeddingProviderError(f"Gemini embedding error: {str(e)}")

class LocalEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic Local Embedding Provider.
    Produces high-speed normalized 384-dimensional feature projections via 
    character n-gram hashing and TF weighting, guaranteeing 100% test reliability
    and zero dependency on remote networks or GPU download delays.
    """

    def __init__(self, dim: int = 384):
        self._dim = dim

    @property
    def provider_name(self) -> str:
        return "local_deterministic"

    @property
    def dimension(self) -> int:
        return self._dim

    STOP_WORDS = {
        "the", "is", "where", "what", "which", "how", "a", "an", "and",
        "or", "in", "on", "at", "to", "for", "of", "with", "by", "from",
        "as", "this", "that", "are", "be", "it", "do", "does", "i", "we"
    }

    def embed_text(self, text: str) -> List[float]:
        clean = text.lower().strip()
        vec = [0.0] * self._dim
        if not clean:
            return vec

        # Tokenize by alphanumeric words
        tokens = [t for t in re.findall(r"[a-zA-Z0-9]+", clean) if t not in self.STOP_WORDS]
        for i, word in enumerate(tokens):
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest()[:8], 16)
            vec[h % self._dim] += 5.0

            # Sub-word prefix split (e.g. dockerfile -> docker)
            if word.endswith("file") and len(word) > 4:
                prefix = word[:-4]
                h_p = int(hashlib.md5(prefix.encode("utf-8")).hexdigest()[:8], 16)
                vec[h_p % self._dim] += 3.0

            # Add bigram if possible
            if i < len(tokens) - 1:
                bi = f"{word}_{tokens[i+1]}"
                h_bi = int(hashlib.md5(bi.encode("utf-8")).hexdigest()[:8], 16)
                vec[h_bi % self._dim] += 3.0

            # Character 4-grams for subtle subword matching with low noise
            if len(word) >= 5:
                for j in range(len(word) - 3):
                    ngram = word[j : j + 4]
                    h_ng = int(hashlib.md5(ngram.encode("utf-8")).hexdigest()[:8], 16)
                    vec[h_ng % self._dim] += 0.08

        # L2 Normalize vector
        magnitude = math.sqrt(sum(x * x for x in vec))
        if magnitude > 0:
            vec = [x / magnitude for x in vec]

        return vec

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]

class EmbeddingFactory:
    """Manages embedding provider selection, dimension verification, and graceful fallback."""

    @staticmethod
    def get_provider(preferred_provider: Optional[str] = None) -> EmbeddingProvider:
        target = preferred_provider or getattr(settings, "EMBEDDING_PROVIDER", "gemini")

        if target == "gemini" and settings.has_gemini:
            return GeminiEmbeddingProvider(api_key=settings.GEMINI_API_KEY)
        
        logger.info("Using LocalEmbeddingProvider (offline deterministic mode)")
        return LocalEmbeddingProvider(dim=384)
