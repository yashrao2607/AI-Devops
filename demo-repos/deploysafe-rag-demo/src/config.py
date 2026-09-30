import os

class AppConfig:
    PORT: int = int(os.getenv("PORT", "8080"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-do-not-use-in-production")
    APP_ENV: str = os.getenv("APP_ENV", "development")

config = AppConfig()
