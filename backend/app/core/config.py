import os
from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application settings
    PROJECT_NAME: str = "DeploySafe"
    VERSION: str = "0.1.0"
    APP_ENV: str = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")
    API_PORT: int = Field(default=8000)
    API_HOST: str = Field(default="0.0.0.0")
    FRONTEND_URL: str = Field(default="http://localhost:5173")

    # LLM Settings
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    GROQ_API_KEY: Optional[str] = Field(default=None)
    GITHUB_TOKEN: Optional[str] = Field(default=None)

    PRIMARY_LLM_PROVIDER: Literal["gemini", "groq"] = Field(default="gemini")
    FALLBACK_LLM_PROVIDER: Literal["gemini", "groq"] = Field(default="groq")

    GEMINI_MODEL: str = Field(default="gemini-2.5-flash")
    GROQ_MODEL: str = Field(default="openai/gpt-oss-120b")

    # Storage Settings
    DATABASE_URL: str = Field(default="sqlite:///./deploysafe.db")
    CHROMA_PATH: str = Field(default="./chroma_db")

    @property
    def has_gemini(self) -> bool:
        return bool(self.GEMINI_API_KEY and self.GEMINI_API_KEY.strip() and not self.GEMINI_API_KEY.startswith("YOUR_"))

    @property
    def has_groq(self) -> bool:
        return bool(self.GROQ_API_KEY and self.GROQ_API_KEY.strip() and not self.GROQ_API_KEY.startswith("YOUR_"))

    @property
    def has_github(self) -> bool:
        return bool(self.GITHUB_TOKEN and self.GITHUB_TOKEN.strip() and not self.GITHUB_TOKEN.startswith("YOUR_"))

    def get_active_provider(self) -> str:
        """Determines the active provider based on priority and configuration."""
        if self.PRIMARY_LLM_PROVIDER == "gemini" and self.has_gemini:
            return "gemini"
        if self.PRIMARY_LLM_PROVIDER == "groq" and self.has_groq:
            return "groq"
        if self.FALLBACK_LLM_PROVIDER == "groq" and self.has_groq:
            return "groq"
        if self.FALLBACK_LLM_PROVIDER == "gemini" and self.has_gemini:
            return "gemini"
        return "diagnostic_mock"

settings = Settings()
