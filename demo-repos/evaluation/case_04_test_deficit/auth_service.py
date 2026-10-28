import hashlib

class PaymentAuthorizationService:
    """Critical financial transaction service."""

    def authorize_transaction(self, account_id: str, amount: float, signature: str) -> bool:
        if amount <= 0:
            return False
        # Sensitive cryptographic signing logic without unit tests
        expected = hashlib.sha256(f"{account_id}:{amount}".encode()).hexdigest()
        return signature == expected

    def refund_transaction(self, tx_id: str, amount: float) -> bool:
        # Untested refund processing
        return True
