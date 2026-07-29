"""Test per src/models/recommender.py: motore di raccomandazione content-based."""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import pytest

from src.models.recommender import WineRecommender, FEATURES


def fake_wine_data() -> pd.DataFrame:
    rows = []
    base = {f: 5.0 for f in FEATURES}
    for i, drift in enumerate([0.0, 0.1, 1.0, 5.0]):
        row = {**base}
        row.update({f: base[f] + drift for f in FEATURES})
        row.update({
            "id": i + 1, "name": f"Vino Rosso {i + 1}", "type": "red",
            "price_eur": 10.0 + i * 5, "food_pairing": "test", "quality": 6,
        })
        rows.append(row)

    white = {**base}
    white.update({
        "id": 99, "name": "Vino Bianco", "type": "white",
        "price_eur": 8.0, "food_pairing": "test", "quality": 6,
    })
    rows.append(white)
    return pd.DataFrame(rows)


@pytest.fixture
def recommender(monkeypatch):
    monkeypatch.setattr(WineRecommender, "_load", staticmethod(fake_wine_data))
    return WineRecommender()


def test_recommend_excludes_the_wine_itself(recommender):
    result = recommender.recommend(wine_id=1, top_n=3, same_type=True)
    assert 1 not in result["id"].values


def test_recommend_orders_by_similarity_descending(recommender):
    result = recommender.recommend(wine_id=1, top_n=3, same_type=True)
    ordered_ids = result["id"].tolist()
    assert ordered_ids.index(2) < ordered_ids.index(4)


def test_recommend_same_type_excludes_other_type(recommender):
    result = recommender.recommend(wine_id=1, top_n=10, same_type=True)
    assert 99 not in result["id"].values


def test_recommend_raises_for_unknown_wine_id(recommender):
    with pytest.raises(ValueError):
        recommender.recommend(wine_id=9999)


def test_find_cheaper_alternative_only_returns_cheaper_wines(recommender):
    result = recommender.find_cheaper_alternative(wine_id=4)
    if not result.empty:
        assert (result["price_eur"] < 25.0).all()


def test_find_cheaper_alternative_empty_when_base_is_cheapest(recommender):
    result = recommender.find_cheaper_alternative(wine_id=1)
    assert result.empty


def test_find_cheaper_alternative_raises_for_unknown_wine_id(recommender):
    with pytest.raises(ValueError):
        recommender.find_cheaper_alternative(wine_id=9999)
