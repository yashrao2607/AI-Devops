import pytest
from backend.app.services.rag.embeddings import LocalEmbeddingProvider, GeminiEmbeddingProvider, EmbeddingFactory, EmbeddingProviderError

def test_local_embedding_provider_dimension_and_normalization():
    provider = LocalEmbeddingProvider(dim=384)
    assert provider.dimension == 384
    assert provider.provider_name == "local_deterministic"

    vec = provider.embed_text("DeploySafe deployment readiness check")
    assert len(vec) == 384
    assert isinstance(vec[0], float)

    # Check vector magnitude is approximately 1.0 (L2 normalized)
    mag = sum(x * x for x in vec)
    assert abs(mag - 1.0) < 1e-4

def test_local_embedding_batch():
    provider = LocalEmbeddingProvider(dim=384)
    texts = ["Docker deployment", "PostgreSQL database configuration", "pytest testing command"]
    batch_vecs = provider.embed_batch(texts)
    assert len(batch_vecs) == 3
    assert len(batch_vecs[0]) == 384

def test_gemini_missing_key_raises():
    provider = GeminiEmbeddingProvider(api_key="")
    with pytest.raises(EmbeddingProviderError):
        provider.embed_text("Test query")

def test_embedding_factory_fallback():
    # Without Gemini key, factory should fall back to LocalEmbeddingProvider
    provider = EmbeddingFactory.get_provider()
    assert provider.dimension in (384, 768)
    vec = provider.embed_text("Factory test")
    assert len(vec) == provider.dimension
