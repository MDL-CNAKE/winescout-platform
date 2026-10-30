"""Test delle funzioni di formattazione dell'interfaccia Streamlit."""
from src.ui.formato import (abbinamenti, descrivi_criteri, descrivi_metriche, euro,
                            livello_conservazione, lotto_vino, titolo_vino)


def test_titolo_e_lotto_separati():
    nome = "Rosso Corposo Armonico - Lotto #0042"
    assert titolo_vino(nome) == "Rosso Corposo Armonico"
    assert lotto_vino(nome) == "#0042"


def test_nome_senza_lotto():
    assert titolo_vino("Bianco Fresco") == "Bianco Fresco"
    assert lotto_vino("Bianco Fresco") is None


def test_euro_con_virgola_decimale():
    assert euro(12.5) == "12,50 €"
    assert euro(1234.5) == "1.234,50 €"
    assert euro(None) == "—"


def test_livelli_con_le_soglie_del_backend():
    # Stesse soglie di src/conservation.py: 75 e 45.
    assert livello_conservazione(75) == "buono"
    assert livello_conservazione(74) == "attenzione"
    assert livello_conservazione(45) == "attenzione"
    assert livello_conservazione(44) == "critico"


def test_abbinamenti_divisi_per_piatto():
    assert abbinamenti("Brasato, cinghiale in umido ,  ") == ["Brasato", "cinghiale in umido"]
    assert abbinamenti(None) == []


def test_criteri_di_un_profilo():
    p = {"wine_type": "white", "min_quality": 6, "max_price": 20.0}
    assert descrivi_criteri(p) == "bianchi · qualità ≥ 6 · prezzo ≤ 20.0 €"
    assert descrivi_criteri({}) == "nessun vincolo: tutto il catalogo"


def test_metriche_parziali():
    # In modalita' demo il backend restituisce solo il tempo di recupero.
    assert descrivi_metriche({"ms_recupero": 40}) == "recupero 40 ms"
    assert descrivi_metriche(None) == ""
