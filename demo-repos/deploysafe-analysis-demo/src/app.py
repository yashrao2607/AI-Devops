from fastapi import FastAPI

app = FastAPI(title="PaymentCheckoutService")

@app.get("/")
def health():
    return {"status": "ok", "service": "PaymentCheckoutService"}
