import os

def calculate_tax(amount: float, rate: float = 0.05) -> float:
    if amount < 0 or rate < 0:
        raise ValueError("Amount and rate must be non-negative")
    return round(amount * rate, 2)
