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


def test_descrizione_card_dai_dati():
    from src.ui.formato import descrizione_card
    v = {"id": 1, "type": "red", "alcohol": 12.4, "residual_sugar": 2.0, "fixed_acidity": 7.0,
         "ph": 3.4, "food_pairing": "Brasato al Barolo, cinghiale in umido"}
    # id 1 su due piatti: la rotazione sceglie il secondo.
    assert descrizione_card(v) == ("Un rosso corposo, secco, 12.4% vol con pH 3.40. "
                                   "Da provare con cinghiale in umido.")


def test_dolcezza_con_correzione_per_acidita():
    from src.ui.formato import dolcezza
    assert dolcezza(3, 5) == "secco"
    assert dolcezza(8, 7) == "secco"       # acido abbastanza da sembrare secco
    assert dolcezza(8, 5) == "abboccato"
    assert dolcezza(30, 6) == "amabile"
    assert dolcezza(50, 6) == "dolce"


def test_metriche_parziali():
    # In modalita' demo il backend restituisce solo il tempo di recupero.
    assert descrivi_metriche({"ms_recupero": 40}) == "recupero 40 ms"
    assert descrivi_metriche(None) == ""
