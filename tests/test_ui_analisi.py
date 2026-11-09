"""Test delle aggregazioni del cruscotto vendite (src/ui/analisi.py)."""
from src.ui import analisi

VINI = [
    {"id": 1, "type": "red", "quality": 5, "price_eur": 9.5, "margin_pct": 66.0},
    {"id": 2, "type": "red", "quality": 7, "price_eur": 24.0, "margin_pct": 42.0},
    {"id": 3, "type": "white", "quality": 6, "price_eur": 12.0, "margin_pct": 63.0},
    {"id": 4, "type": "white", "quality": 6, "price_eur": None, "margin_pct": None},
]


def test_lotti_senza_prezzo_esclusi():
    # Un lotto senza prezzo non puo' stare in una fascia ne' in un margine.
    assert len(analisi.prepara(VINI)) == 3


def test_filtro_per_tipo():
    assert set(analisi.prepara(VINI, "red")["Tipo"]) == {"Rosso"}


def test_fasce_con_estremo_sinistro_incluso():
    df = analisi.prepara(VINI)
    assert dict(zip(df["id"], df["Fascia"].astype(str))) == {1: "< 10 €", 2: "20–25 €", 3: "10–15 €"}


def test_margine_in_euro():
    df = analisi.prepara(VINI)
    assert round(df.loc[df["id"] == 2, "Margine €"].iloc[0], 2) == 10.08


def test_indicatori():
    k = analisi.indicatori(analisi.prepara(VINI))
    assert k["lotti"] == 3
    assert round(k["prezzo_medio"], 2) == 15.17


def test_i_due_margini_vanno_in_direzioni_opposte():
    # E' l'affermazione della nota nel cruscotto: deve restare vera sui dati.
    m = analisi.margini_per_fascia(analisi.prepara(VINI)).set_index("Fascia")
    assert m.loc["< 10 €", "Margine %"] > m.loc["20–25 €", "Margine %"]
    assert m.loc["< 10 €", "Margine €"] < m.loc["20–25 €", "Margine €"]


def test_categorie_vuote_incluse_nei_conteggi():
    # Nella mappa una fascia senza lotti deve comparire come cella vuota,
    # non sparire: anche l'assenza e' un'informazione.
    conteggi = analisi.lotti_per(analisi.prepara(VINI), "Fascia")
    assert len(conteggi) == len(analisi.ETICHETTE_FASCE) * 2
