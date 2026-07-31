"""Test per src/naming.py: nomi descrittivi generati dalla chimica del vino."""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from src.naming import build_name, second_descriptor
from src.wine_style import acidity_category, body_category, sweetness_category


def test_body_thresholds():
    assert body_category(12.0) == "corposo"
    assert body_category(15.0) == "corposo"
    assert body_category(9.5) == "leggero"
    assert body_category(8.0) == "leggero"
    assert body_category(10.5) == "equilibrato"


def test_sweetness_follows_eu_thresholds():
    # Sotto i 4 g/L e' secco a prescindere dall'acidita'.
    assert sweetness_category(3.0, acidity=5.0) == "secco"
    # Fra 4 e 9 g/L resta secco solo se l'acidita' compensa.
    assert sweetness_category(8.0, acidity=7.0) == "secco"
    assert sweetness_category(8.0, acidity=4.0) == "abboccato"
    # Oltre i 12 g/L (senza compensazione) si entra fra gli amabili.
    assert sweetness_category(20.0, acidity=5.0) == "amabile"
    # Dolce vero solo oltre i 45 g/L.
    assert sweetness_category(50.0, acidity=6.0) == "dolce"
    assert sweetness_category(44.0, acidity=6.0) == "amabile"


def test_acidity_descriptor_from_ph():
    assert acidity_category(3.0) == "fresco"
    assert acidity_category(3.5) == "morbido"
    assert acidity_category(3.3) == "armonico"


def test_secco_non_compare_nel_nome():
    """Un vino secco porta la freschezza, non la dicitura 'Secco'."""
    assert second_descriptor(sugar=2.0, acidity=6.0, ph=3.0) == "Fresco"
    assert second_descriptor(sugar=2.0, acidity=6.0, ph=3.5) == "Morbido"


def test_non_secco_porta_la_dolcezza():
    assert second_descriptor(sugar=20.0, acidity=5.0, ph=3.3) == "Amabile"
    assert second_descriptor(sugar=50.0, acidity=6.0, ph=3.3) == "Dolce"


def test_build_name_red():
    row = pd.Series({
        "type": "red", "alcohol": 13.0, "residual_sugar": 1.5,
        "fixed_acidity": 7.0, "ph": 3.0, "quality": 8,
    })
    assert build_name(row, wine_id=42) == "Rosso Corposo Fresco - Lotto #0042"


def test_build_name_white():
    row = pd.Series({
        "type": "white", "alcohol": 10.0, "residual_sugar": 20.0,
        "fixed_acidity": 5.0, "ph": 3.3, "quality": 6,
    })
    assert build_name(row, wine_id=7) == "Bianco Equilibrato Amabile - Lotto #0007"


def test_riserva_non_compare_mai_nel_nome():
    """'Riserva' indica per legge un affinamento minimo fissato dal
    disciplinare, informazione assente dal dataset: non puo' essere usata
    come sinonimo di punteggio alto, nemmeno per la qualita' massima."""
    row = pd.Series({
        "type": "red", "alcohol": 13.0, "residual_sugar": 1.0,
        "fixed_acidity": 7.0, "ph": 3.0, "quality": 9,
    })
    assert "Riserva" not in build_name(row, wine_id=1)


def test_build_name_id_is_zero_padded():
    row = pd.Series({
        "type": "red", "alcohol": 10.0, "residual_sugar": 3.0,
        "fixed_acidity": 6.0, "ph": 3.3, "quality": 5,
    })
    assert "#0008" in build_name(row, wine_id=8)


def test_corposo_dolce_non_e_piu_producibile_con_dati_del_dataset():
    """Nel dataset lo zucchero massimo e' 65,8 g/L ma i vini oltre i 45 g/L
    sono uno solo: la combinazione 'Corposo Dolce', che con le vecchie
    soglie arbitrarie compariva 39 volte, resta possibile solo per vini
    realmente da dessert. Vedi docs/model_limitations.md."""
    row = pd.Series({
        "type": "white", "alcohol": 13.0, "residual_sugar": 12.0,
        "fixed_acidity": 6.0, "ph": 3.2, "quality": 6,
    })
    assert "Dolce" not in build_name(row, wine_id=1)
