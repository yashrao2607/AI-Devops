from fastapi import FastAPI
from .config import config

app = FastAPI(title="DemoMicroservice", version="1.0.0")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "demo-microservice",
        "port": config.PORT,
        "environment": config.APP_ENV
    }

@app.get("/items")
def list_items():
    return [{"id": 1, "name": "Standard Item"}]
