"""Shared fixtures for projection tests."""
from datetime import date

import pytest


@pytest.fixture
def sample_purchases():
    """Three purchases across two months, contracted at IPCA+6% and IPCA+7%."""
    return [
        {"date": date(2024, 1, 15), "qty": 0.05, "price": 1000.0,
         "invested": 50.0, "spread": 0.06, "mkt_gross": 60.0, "days": 1,
         "ir_rate": 0.15, "ir_tax": 0.0, "b3_fee": 0.0, "mkt_net": 60.0},
        {"date": date(2024, 1, 20), "qty": 0.10, "price": 1000.0,
         "invested": 100.0, "spread": 0.06, "mkt_gross": 120.0, "days": 1,
         "ir_rate": 0.15, "ir_tax": 0.0, "b3_fee": 0.0, "mkt_net": 120.0},
        {"date": date(2024, 3, 10), "qty": 0.20, "price": 1000.0,
         "invested": 200.0, "spread": 0.07, "mkt_gross": 240.0, "days": 1,
         "ir_rate": 0.15, "ir_tax": 0.0, "b3_fee": 0.0, "mkt_net": 240.0},
    ]


@pytest.fixture
def empty_holidays():
    return set()
