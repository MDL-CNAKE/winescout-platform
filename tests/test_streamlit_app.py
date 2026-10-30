"""Test dell'interfaccia Streamlit con un backend finto.

L'interfaccia non contiene logica di dominio, quindi qui non si verifica che
i numeri siano giusti (lo fanno i test del backend): si verifica che ogni
pagina si apra senza eccezioni con risposte di forma reale, e che gli errori
del backend arrivino all'utente come messaggi leggibili.

Le risposte finte riproducono la forma dei modelli Pydantic di
backend/main.py. Se un endpoint cambia forma, questi test devono cambiare
con lui: e' il loro scopo.
"""
import json
import os

import pytest
import requests

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

RADICE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

VINI = [
    {"id": 1, "name": "Rosso Equilibrato Armonico - Lotto #0001", "type": "red", "alcohol": 9.4,
     "ph": 3.51, "residual_sugar": 1.9, "fixed_acidity": 7.4, "volatile_acidity": 0.7,
     "chlorides": 0.076, "sulphates": 0.56, "quality": 5, "price_eur": 14.2, "margin_pct": 55.0,
     "food_pairing": "Tagliatelle al ragu, tagliere di salumi"},
    {"id": 2, "name": "Bianco Corposo Fresco - Lotto #0002", "type": "white", "alcohol": 12.8,
     "ph": 3.1, "residual_sugar": 2.0, "fixed_acidity": 6.8, "volatile_acidity": 0.3,
     "chlorides": 0.04, "sulphates": 0.5, "quality": 7, "price_eur": 21.0, "margin_pct": 44.0,
     "food_pairing": "Branzino al forno, risotto ai frutti di mare"},
]


def _risposta(stato: int, corpo) -> requests.Response:
    r = requests.Response()
    r.status_code = stato
    r._content = corpo if isinstance(corpo, bytes) else json.dumps(corpo).encode()
    return r


def _backend_finto(metodo: str, url: str, params=None, json=None, timeout=None):  # noqa: A002
    percorso = url.split("://", 1)[1].split("/", 1)[1]
    percorso = "/" + percorso
    tabella = {
        ("GET", "/api/health"): {"status": "ok"},
        ("GET", "/api/operators"): [{"id": 1, "name": "Meg", "role": "titolare"}],
        ("GET", "/api/favorites"): [{"wine_id": 1, "operator_id": 1, "operator_name": "Meg"}],
        ("GET", "/api/wines/summary"): [{"id": v["id"], "name": v["name"], "type": v["type"]} for v in VINI],
        ("GET", "/api/wines/facets"): {"alcohol": [8.0, 14.9], "residual_sugar": [0.6, 65.8],
                                       "fixed_acidity": [3.8, 15.9], "price_eur": [4.8, 40.2],
                                       "quality": [3, 9]},
        ("GET", "/api/wines/search"): {"items": VINI, "total": 2, "page": 1, "page_size": 50},
        ("GET", "/api/wines/1"): VINI[0],
        ("GET", "/api/recommend/1"): [{**{k: VINI[1][k] for k in ("id", "name", "type", "alcohol", "ph",
                                                                 "quality", "price_eur")},
                                       "similarity": 0.93}],
        ("GET", "/api/recommend/1/cheaper"): [],
        ("GET", "/api/packaging"): [{"id": 1, "name": VINI[0]["name"], "type": "red", "quality": 5,
                                     "price_eur": 14.2, "style": "Moderno",
                                     "bottle_format": "Standard 750ml", "cap_type": "Tappo sintetico",
                                     "label_material": "Carta patinata minimal"}],
        ("GET", "/api/packaging/1"): {"id": 1, "name": VINI[0]["name"], "type": "red", "quality": 5,
                                      "price_eur": 14.2, "style": "Moderno",
                                      "bottle_format": "Standard 750ml", "cap_type": "Tappo sintetico",
                                      "label_material": "Carta patinata minimal"},
        ("GET", "/api/conservazione"): [{"id": 1, "name": VINI[0]["name"], "type": "red", "quality": 5,
                                         "price_eur": 14.2, "punteggio": 38,
                                         "giudizio": "Da immettere sul mercato"}],
        ("GET", "/api/conservazione/1"): {
            "id": 1, "name": VINI[0]["name"], "type": "red", "quality": 5, "price_eur": 14.2,
            "punteggio": 38, "giudizio": "Da immettere sul mercato",
            "indicatori": [{"nome": "pH", "valore": 3.51, "unita": "", "livello": "attenzione",
                            "spiegazione": "pH intermedio."}]},
        ("GET", "/api/leve/1"): {"id": 1, "name": VINI[0]["name"], "qualita_reale": 5,
                                 "previsione_attuale": 5.12, "leve": [{
                                     "campo": "alcohol", "etichetta": "Grado alcolico", "unita": "% vol",
                                     "valore_attuale": 9.4, "valore_proposto": 9.9, "variazione": 0.5,
                                     "delta_qualita": 0.21, "direzione": "aumentare",
                                     "intervento": "Momento della vendemmia."}]},
        ("GET", "/api/importanza"): [{"campo": "alcohol", "etichetta": "Grado alcolico",
                                      "importanza": 0.497, "incertezza": 0.02, "quota": 38.7,
                                      "significato": "Proxy della maturazione."}],
        ("GET", "/api/profili"): [{"id": 1, "name": "Nord Europa", "notes": None, "wine_type": "white",
                                   "min_quality": 6, "min_alcohol": None, "max_alcohol": None,
                                   "max_sugar": 4.0, "min_acidity": None, "max_price": 20.0}],
        ("GET", "/api/profili/1/vini"): [{"id": 2, "name": VINI[1]["name"], "type": "white", "quality": 7,
                                          "alcohol": 12.8, "residual_sugar": 2.0, "fixed_acidity": 6.8,
                                          "price_eur": 21.0, "margin_pct": 44.0, "margine_euro": 9.24}],
        ("POST", "/api/predict"): {"quality": 5.4},
        ("POST", "/api/sommelier"): {
            "answer": "Con la carbonara serve acidità che sgrassi.", "demo_mode": False,
            "sources": ["Grassezza e untuosita del cibo\n\nL'acidità contrasta la grassezza."],
            "metriche": {"ms_recupero": 40, "ms_generazione": 900, "token_prompt": 800,
                         "token_risposta": 60, "modello": "finto"},
            "messaggi_ricordati": len((json or {}).get("storico", []))},
        ("POST", "/api/agente"): {
            "answer": "In catalogo c'è un rosso sotto i 15 euro.",
            "passi": [{"strumento": "cerca_vini", "argomenti": {"tipo": "red", "prezzo_massimo": 15},
                       "risultati": 1}],
            "metriche": {"ms_generazione": 1200}},
        ("POST", "/api/verdetto"): {
            "verdetto": {"giudizio": "accettabile", "motivazione": "Struttura leggera.",
                         "dato_citato": "9,4% vol", "profilo_alternativo": "più corpo"},
            "tentativi": 1, "metriche": {"ms_generazione": 700}},
    }
    corpo = tabella.get((metodo, percorso))
    if corpo is None:
        return _risposta(404, {"detail": f"Percorso non previsto dal test: {metodo} {percorso}"})
    return _risposta(200, corpo)


@pytest.fixture(autouse=True)
def cache_vuota():
    # Le letture dell'interfaccia sono in cache, e la cache di Streamlit vive
    # nel processo: senza svuotarla un test vedrebbe le risposte del
    # precedente (per esempio un backend "attivo" in un test dove e' spento).
    import streamlit as st
    st.cache_data.clear()
    yield
    st.cache_data.clear()


@pytest.fixture
def backend(monkeypatch):
    """Backend finto che registra le richieste ricevute."""
    ricevute: list[tuple[str, str, dict | None]] = []

    def registra(metodo, url, params=None, json=None, timeout=None):  # noqa: A002
        ricevute.append((metodo, "/" + url.split("://", 1)[1].split("/", 1)[1], json))
        return _backend_finto(metodo, url, params=params, json=json, timeout=timeout)

    monkeypatch.setattr(requests, "request", registra)
    return ricevute


def _apri(chiave: str) -> AppTest:
    """Esegue una sola pagina con la navigazione completa del titolare."""
    def script(chiave, radice):
        import sys
        sys.path.insert(0, radice)
        import streamlit as st
        from src.ui import navigazione
        st.navigation(navigazione.pagine_per_ruolo("titolare"), position="hidden")
        navigazione.SEZIONI[chiave][2]()

    at = AppTest.from_function(script, args=(chiave, RADICE), default_timeout=30)
    at.session_state["vino_scelto"] = 1
    at.session_state["operatore_id"] = 1
    return at.run()


@pytest.mark.parametrize("chiave", [
    "catalogo", "vino", "sveva", "predizione", "modello",
    "conservazione", "vendite", "packaging", "spedizioni", "marketing",
])
def test_ogni_pagina_si_apre_senza_eccezioni(backend, chiave):
    at = _apri(chiave)
    assert not at.exception, at.exception
    assert not at.error, [e.value for e in at.error]


def test_predizione_invia_tutti_i_parametri(backend):
    at = _apri("predizione")
    at.button[0].click().run()
    assert not at.exception
    assert at.session_state["pred_nuovo"] == 5.4
    payload = next(j for m, p, j in backend if p == "/api/predict")
    # Il modello e' addestrato su 12 colonne: ne mancasse una, il backend
    # restituirebbe un errore invece di una stima.
    assert len(payload) == 12 and payload["type"] == "red"


def test_sveva_ricorda_la_conversazione(backend):
    at = _apri("sveva")
    at.chat_input[0].set_value("cosa bevo con una carbonara?").run()
    at.chat_input[0].set_value("e con il pesce?").run()
    assert not at.exception

    inviate = [j for m, p, j in backend if p == "/api/sommelier"]
    # Prima domanda senza storico, seconda con lo scambio precedente: e' il
    # client a portare la memoria, il backend resta senza stato.
    assert inviate[0]["storico"] == []
    assert [m["ruolo"] for m in inviate[1]["storico"]] == ["user", "assistant"]
    assert inviate[1]["question"] == "e con il pesce?"
    assert len(at.session_state["sveva_storico"]) == 4


def test_sveva_mostra_gli_strumenti_usati(backend):
    def script(radice):
        import sys
        sys.path.insert(0, radice)
        import streamlit as st
        from src.ui import navigazione
        st.navigation(navigazione.pagine_per_ruolo("titolare"), position="hidden")
        navigazione.SEZIONI["sveva"][2]()

    at = AppTest.from_function(script, args=(RADICE,), default_timeout=30)
    at.session_state["sveva_modalita"] = "catalogo"
    at.run()
    at.text_area[0].set_value("quali rossi ho sotto i 15 euro?")
    at.button[0].click().run()
    assert not at.exception
    assert any("cerca_vini" in m.value for m in at.markdown)


def test_verdetto_nella_scheda_vino(backend):
    at = _apri("vino")
    at.text_input[0].set_value("pizza margherita")
    bottone = next(b for b in at.button if b.label == "Valuta")
    bottone.click().run()
    assert not at.exception
    assert any("Accettabile" in w.value for w in at.warning)


def test_app_completa_si_avvia(backend):
    at = AppTest.from_file(os.path.join(RADICE, "src", "app.py"), default_timeout=30).run()
    assert not at.exception, at.exception
    assert any("Catalogo" in t.value for t in at.title)


def test_backend_spento_mostra_istruzioni(monkeypatch):
    def spento(*args, **kwargs):
        raise requests.ConnectionError("rifiutata")

    monkeypatch.setattr(requests, "request", spento)
    at = AppTest.from_file(os.path.join(RADICE, "src", "app.py"), default_timeout=30)
    at.run()
    assert not at.exception
    assert any("non risponde" in e.value for e in at.error)


def test_errore_del_backend_arriva_con_il_suo_messaggio(monkeypatch):
    from src.ui import api

    monkeypatch.setattr(requests, "request",
                        lambda *a, **k: _risposta(404, {"detail": "Vino con id=99 non trovato"}))
    with pytest.raises(api.ApiError) as e:
        api.richiesta("GET", "/api/wines/99")
    assert str(e.value) == "Vino con id=99 non trovato"
    assert e.value.stato == 404
