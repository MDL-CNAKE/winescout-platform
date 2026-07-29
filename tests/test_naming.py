"""Test per src/naming.py: nomi descrittivi generati dalla chimica del vino."""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from src.naming import alcohol_descriptor, sugar_descriptor, build_name


def test_alcohol_descriptor_thresholds():
    assert alcohol_descriptor(12.0) == "Corposo"
    assert alcohol_descriptor(15.0) == "Corposo"
    assert alcohol_descriptor(9.5) == "Leggero"
    assert alcohol_descriptor(8.0) == "Leggero"
    assert alcohol_descriptor(10.5) == "Equilibrato"


def test_sugar_descriptor_thresholds():
    assert sugar_descriptor(10.0) == "Dolce"
    assert sugar_descriptor(50.0) == "Dolce"
    assert sugar_descriptor(2.0) == "Secco"
    assert sugar_descriptor(0.5) == "Secco"
    assert sugar_descriptor(5.0) == "Amabile"


def test_build_name_red_riserva():
    row = pd.Series({"type": "red", "alcohol": 13.0, "residual_sugar": 1.5, "quality": 8})
    name = build_name(row, wine_id=42)
    assert name == "Rosso Corposo Secco Riserva - Lotto #0042"


def test_build_name_white_no_riserva_below_quality_7():
    row = pd.Series({"type": "white", "alcohol": 10.0, "residual_sugar": 3.0, "quality": 6})
    name = build_name(row, wine_id=7)
    assert name == "Bianco Equilibrato Amabile - Lotto #0007"
    assert "Riserva" not in name


def test_build_name_id_is_zero_padded():
    row = pd.Series({"type": "red", "alcohol": 10.0, "residual_sugar": 3.0, "quality": 5})
    name = build_name(row, wine_id=8)
    assert "#0008" in name
