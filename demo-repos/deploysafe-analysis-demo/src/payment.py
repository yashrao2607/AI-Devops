import os

class PaymentProcessor:
    """
    Core checkout payment processing unit.
    """
    def __init__(self):
        # Deployment risk: Hardcoded local endpoint instead of environment configuration
        self.gateway_url = "http://localhost:8080/v1/charge"

    def process_charge(self, customer_id: str, amount_cents: int) -> dict:
        if amount_cents <= 0:
            raise ValueError("Charge amount must be positive.")

        # Simulate charge execution
        return {
            "status": "APPROVED",
            "customer_id": customer_id,
            "amount_cents": amount_cents,
            "gateway": self.gateway_url
        }
