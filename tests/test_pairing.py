"""Test per src/pairing.py: le regole di abbinamento cibo-vino."""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from src.pairing import pairing_for


def wine(type_, alcohol, sugar, acidity=6.0):
    return pd.Series({
        "type": type_, "alcohol": alcohol,
        "residual_sugar": sugar, "fixed_acidity": acidity,
    })


def test_true_dessert_wine_above_eu_sweet_threshold():
    """Dolce da dessert solo oltre i 45 g/L (Reg. UE 2019/33)."""
    result = pairing_for(wine("white", alcohol=11, sugar=50))
    assert "dessert" in result.lower() or "dolci" in result.lower()


def test_amabile_wine_is_not_dessert_pairing():
    result = pairing_for(wine("white", alcohol=11, sugar=20))
    assert "dessert" not in result.lower()
    assert "speziat" in result.lower() or "agrodolce" in result.lower()


def test_abboccato_non_e_trattato_come_dolce():
    """Con le vecchie soglie un vino a 15 g/L finiva fra i dolci da
    dessert; con il criterio UE resta un abboccato e segue le regole di
    struttura."""
    result = pairing_for(wine("white", alcohol=11, sugar=11, acidity=5.0))
    assert "dessert" not in result.lower()


def test_red_full_bodied_gets_structured_dish():
    result = pairing_for(wine("red", alcohol=13, sugar=2))
    assert "brasato" in result.lower() or "cinghiale" in result.lower()


def test_red_light_gets_everyday_dish():
    result = pairing_for(wine("red", alcohol=10, sugar=2))
    assert "tagliatelle" in result.lower() or "salumi" in result.lower()


def test_white_high_acidity_gets_fried_food():
    result = pairing_for(wine("white", alcohol=10, sugar=2, acidity=8.0))
    assert "fritto" in result.lower() or "vongole" in result.lower()


def test_white_full_bodied_low_acidity_gets_seafood():
    result = pairing_for(wine("white", alcohol=13, sugar=2, acidity=5.0))
    assert "branzino" in result.lower() or "risotto" in result.lower()


def test_white_light_default_gets_delicate_dish():
    result = pairing_for(wine("white", alcohol=9, sugar=2, acidity=5.0))
    assert "antipasti" in result.lower() or "orata" in result.lower()
