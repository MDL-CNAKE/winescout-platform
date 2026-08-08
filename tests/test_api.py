"""Test smoke sull'API FastAPI (backend/main.py), con modello/recommender/RAG finti."""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient

import backend.main as backend_main


class FakeModel:
    def predict(self, df):
        return [6.5]


class FakeRecommender:
    def recommend(self, wine_id, top_n=5, same_type=True):
        if wine_id == 9999:
            raise ValueError(f"Vino con id={wine_id} non trovato nel catalogo")
        import pandas as pd
        return pd.DataFrame([{
            "id": 2, "name": "Vino Finto", "type": "red", "alcohol": 12.0,
            "ph": 3.3, "quality": 6, "price_eur": 15.0, "similarity": 0.9,
        }])

    def find_cheaper_alternative(self, wine_id, max_candidates=10):
        if wine_id == 9999:
            raise ValueError(f"Vino con id={wine_id} non trovato nel catalogo")
        import pandas as pd
        return pd.DataFrame(columns=[
            "id", "name", "type", "alcohol", "ph", "quality",
            "price_eur", "similarity", "savings_pct",
        ])


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(backend_main.joblib, "load", lambda path: FakeModel())
    monkeypatch.setattr(backend_main, "WineRecommender", lambda: FakeRecommender())
    monkeypatch.setattr(backend_main, "KnowledgeRetriever", lambda: (_ for _ in ()).throw(Exception("no index in test")))

    with TestClient(backend_main.app) as c:
        yield c


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_returns_quality_score(client):
    payload = {
        "type": "red", "fixed_acidity": 7.0, "volatile_acidity": 0.5,
        "citric_acid": 0.3, "residual_sugar": 2.0, "chlorides": 0.08,
        "free_sulfur_dioxide": 15.0, "total_sulfur_dioxide": 100.0,
        "density": 0.997, "ph": 3.3, "sulphates": 0.6, "alcohol": 10.0,
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    assert response.json() == {"quality": 6.5}


def test_predict_rejects_missing_field(client):
    payload = {"type": "red"}
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 422


def test_recommend_returns_list(client):
    response = client.get("/api/recommend/1")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Vino Finto"


def test_recommend_unknown_wine_returns_404(client):
    response = client.get("/api/recommend/9999")
    assert response.status_code == 404


def test_cheaper_alternative_empty_list(client):
    response = client.get("/api/recommend/1/cheaper")
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# Il filtro anti-gibberish e' collegato agli endpoint?
#
# I test in tests/test_meaningful_question.py verificano la funzione. Questi
# verificano una cosa diversa e altrettanto necessaria: che sia effettivamente
# applicata. Una funzione corretta ma non richiamata da un endpoint non
# protegge nulla, e nessun test unitario se ne accorgerebbe.
#
# Sono i due endpoint che non dipendono dall'indice RAG: il filtro scatta
# PRIMA di qualsiasi chiamata esterna o controllo della chiave, quindi il
# rifiuto si osserva anche senza LLM configurato. Che sia il primo controllo
# e' il punto: se scattasse dopo, avremmo gia' speso la chiamata.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("spazzatura", ["qwerty", "kkkkkkkk", "12345", "..."])
def test_verdetto_rifiuta_gibberish(client, spazzatura):
    response = client.post(
        "/api/verdetto", json={"wine_id": 1, "piatto": spazzatura}
    )
    assert response.status_code == 400


@pytest.mark.parametrize("spazzatura", ["asdfgh", "jkljkl", "aaaa"])
def test_agente_rifiuta_gibberish(client, spazzatura):
    response = client.post("/api/agente", json={"question": spazzatura})
    assert response.status_code == 400


def test_verdetto_accetta_piatto_di_una_parola(client):
    """Il caso che il filtro precedente sbagliava.

    Senza chiave LLM configurata la risposta attesa e' 503 (servizio non
    disponibile), NON 400 (domanda non valida): significa che "ndole" ha
    superato il filtro ed e' stata fermata piu' avanti, per un motivo
    diverso. Distinguere i due codici e' esattamente il punto del test.
    """
    response = client.post("/api/verdetto", json={"wine_id": 1, "piatto": "ndole"})
    assert response.status_code != 400
