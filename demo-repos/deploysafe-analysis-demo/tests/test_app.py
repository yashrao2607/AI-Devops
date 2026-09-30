from src.app import app

def test_health():
    assert app.title == "PaymentCheckoutService"
