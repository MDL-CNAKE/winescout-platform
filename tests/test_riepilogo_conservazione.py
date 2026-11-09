"""Test del riepilogo di conservazione usato dal cruscotto vendite."""
import pytest
from fastapi.testclient import TestClient

import backend.main as backend_main
from src.conservation import valuta_conservazione


class _Cursore:
    def __init__(self, righe):
        self.righe = righe

    def execute(self, sql, params=None):
        pass

    def fetchall(self):
        return self.righe

    def close(self):
        pass


class _Connessione:
    def __init__(self, righe):
        self.righe = righe

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self, dictionary=False):
        return _Cursore(self.righe)


def _lotto(i, tipo, libera, totale, ph, volatile):
    return {"id": i, "name": f"Lotto {i}", "type": tipo, "quality": 6, "price_eur": 12.0,
            "free_sulfur_dioxide": libera, "total_sulfur_dioxide": totale, "ph": ph,
            "volatile_acidity": volatile}


RIGHE = [
    _lotto(1, "white", 45, 120, 3.1, 0.25),   # ben protetto
    _lotto(2, "white", 40, 110, 3.15, 0.3),   # ben protetto
    _lotto(3, "red", 5, 60, 3.7, 1.0),        # esposto
]


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(backend_main, "DatabaseConnection", lambda: _Connessione(RIGHE))
    monkeypatch.setattr(backend_main.joblib, "load", lambda path: None)
    monkeypatch.setattr(backend_main, "WineRecommender", lambda: None)
    monkeypatch.setattr(
        backend_main, "KnowledgeRetriever",
        lambda: (_ for _ in ()).throw(Exception("nessun indice nei test")),
    )
    with TestClient(backend_main.app) as c:
        yield c


def test_la_rotta_non_viene_letta_come_id(client):
    # Se la rotta stesse dopo /api/conservazione/{wine_id}, "riepilogo" verrebbe
    # interpretato come id e la risposta sarebbe 422.
    assert client.get("/api/conservazione/riepilogo").status_code == 200


def test_conta_ogni_lotto_una_volta(client):
    dati = client.get("/api/conservazione/riepilogo").json()
    assert sum(d["lotti"] for d in dati) == len(RIGHE)


def test_giudizi_dalle_stesse_regole_della_scheda(client):
    # Il riepilogo non ricalcola a modo suo: per ogni lotto deve valere lo
    # stesso giudizio che compare nella scheda del vino.
    attesi: dict[tuple[str, str], int] = {}
    for w in RIGHE:
        g = valuta_conservazione(
            wine_type=w["type"], free_sulfur_dioxide=w["free_sulfur_dioxide"],
            total_sulfur_dioxide=w["total_sulfur_dioxide"], ph=w["ph"],
            volatile_acidity=w["volatile_acidity"],
        ).giudizio
        attesi[(w["type"], g)] = attesi.get((w["type"], g), 0) + 1
    dati = client.get("/api/conservazione/riepilogo").json()
    assert {(d["type"], d["giudizio"]): d["lotti"] for d in dati} == attesi
