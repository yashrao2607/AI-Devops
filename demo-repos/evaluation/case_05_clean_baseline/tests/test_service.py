import pytest
from service import calculate_tax

def test_calculate_tax_valid():
    assert calculate_tax(100.0, 0.10) == 10.0
    assert calculate_tax(50.0, 0.05) == 2.50

def test_calculate_tax_negative():
    with pytest.raises(ValueError):
        calculate_tax(-10.0)
