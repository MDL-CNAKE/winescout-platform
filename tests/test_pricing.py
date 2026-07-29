"""Test per src/pricing.py: la logica di business su prezzo e margine."""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from src.pricing import compute_price, compute_margin, PRICE_RANGE


def make_wine(type_: str, quality: int) -> pd.Series:
    return pd.Series({"type": type_, "quality": quality})


def test_price_stays_within_plausible_range_for_red():
    lo, hi = PRICE_RANGE["red"]
    wine = make_wine("red", quality=6)
    price = compute_price(wine)
    assert lo * 0.8 <= price <= hi * 1.15


def test_price_stays_within_plausible_range_for_white():
    lo, hi = PRICE_RANGE["white"]
    wine = make_wine("white", quality=6)
    price = compute_price(wine)
    assert lo * 0.8 <= price <= hi * 1.15


def test_higher_quality_costs_more_on_average():
    low_quality_prices = [compute_price(make_wine("red", 3)) for _ in range(50)]
    high_quality_prices = [compute_price(make_wine("red", 9)) for _ in range(50)]
    avg_low = sum(low_quality_prices) / len(low_quality_prices)
    avg_high = sum(high_quality_prices) / len(high_quality_prices)
    assert avg_high > avg_low


def test_margin_is_within_declared_bounds():
    lo, hi = PRICE_RANGE["red"]
    for price in (lo, (lo + hi) / 2, hi):
        margin = compute_margin(price, "red")
        assert 25 <= margin <= 70


def test_margin_decreases_as_price_increases():
    lo, hi = PRICE_RANGE["red"]
    margins_cheap = [compute_margin(lo, "red") for _ in range(50)]
    margins_expensive = [compute_margin(hi, "red") for _ in range(50)]
    avg_cheap = sum(margins_cheap) / len(margins_cheap)
    avg_expensive = sum(margins_expensive) / len(margins_expensive)
    assert avg_cheap > avg_expensive
