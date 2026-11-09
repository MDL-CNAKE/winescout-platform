"""Test dell'elenco di modelli e del comportamento sul limite (HTTP 429).

I modelli gratuiti di OpenRouter rispondono spesso 429. Questi test fissano
tre cose: l'elenco arriva a OpenRouter nell'ordine scritto nel .env, il 429
provoca un solo nuovo tentativo, e SVEVA risponde con le regole del sistema
invece di mostrare un errore.
"""
import pytest
import requests
from fastapi.testclient import TestClient

import backend.main as backend_main


def _risposta(stato: int, corpo: dict | None = None) -> requests.Response:
    import json
    r = requests.Response()
    r.status_code = stato
    r._content = json.dumps(corpo or {}).encode()
    return r


RISPOSTA_OK = {"choices": [{"message": {"content": "Un bianco fresco."}}], "model": "finto"}


@pytest.fixture
def chiamate(monkeypatch):
    """Registra i corpi inviati a OpenRouter; le risposte si scelgono per test."""
    registro = {"corpi": [], "risposte": []}

    def finto_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        registro["corpi"].append(json)
        return registro["risposte"].pop(0)

    monkeypatch.setattr(backend_main.requests, "post", finto_post)
    monkeypatch.setattr(backend_main.time, "sleep", lambda s: None)
    return registro


def test_elenco_dal_env(monkeypatch):
    monkeypatch.setenv("LLM_MODELS", "a/uno:free, b/due:free ,")
    assert backend_main.modelli_configurati() == ["a/uno:free", "b/due:free"]


def test_senza_elenco_vale_llm_model(monkeypatch):
    monkeypatch.delenv("LLM_MODELS", raising=False)
    monkeypatch.setenv("LLM_MODEL", "c/tre")
    assert backend_main.modelli_configurati() == ["c/tre"]


def test_elenco_inviato_a_openrouter_in_ordine(monkeypatch, chiamate):
    monkeypatch.setenv("LLM_MODELS", "a/uno,b/due")
    chiamate["risposte"] = [_risposta(200, RISPOSTA_OK)]
    backend_main.chiama_modello("chiave", {"messages": []})
    corpo = chiamate["corpi"][0]
    assert corpo["model"] == "a/uno"
    assert corpo["models"] == ["a/uno", "b/due"]


def test_un_solo_modello_senza_parametro_models(monkeypatch, chiamate):
    monkeypatch.delenv("LLM_MODELS", raising=False)
    monkeypatch.setenv("LLM_MODEL", "a/uno")
    chiamate["risposte"] = [_risposta(200, RISPOSTA_OK)]
    backend_main.chiama_modello("chiave", {"messages": []})
    assert "models" not in chiamate["corpi"][0]


def test_un_429_poi_successo(chiamate):
    chiamate["risposte"] = [_risposta(429), _risposta(200, RISPOSTA_OK)]
    r = backend_main.chiama_modello("chiave", {"messages": []})
    assert r.status_code == 200
    assert len(chiamate["corpi"]) == 2


def test_due_429_limite_dichiarato(chiamate):
    chiamate["risposte"] = [_risposta(429), _risposta(429)]
    with pytest.raises(backend_main.LimiteModelli):
        backend_main.chiama_modello("chiave", {"messages": []})
    # Un solo nuovo tentativo: ogni chiamata in piu' consuma il limite giornaliero.
    assert len(chiamate["corpi"]) == 2


def test_altri_errori_restano_errori(chiamate):
    chiamate["risposte"] = [_risposta(500)]
    with pytest.raises(requests.HTTPError):
        backend_main.chiama_modello("chiave", {"messages": []})


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "chiave-di-test")
    monkeypatch.setattr(backend_main.joblib, "load", lambda path: None)
    monkeypatch.setattr(backend_main, "WineRecommender", lambda: None)
    monkeypatch.setattr(
        backend_main, "KnowledgeRetriever",
        lambda: (_ for _ in ()).throw(Exception("nessun indice nei test")),
    )
    with TestClient(backend_main.app) as c:
        yield c


def test_sveva_risponde_con_le_regole_se_i_modelli_sono_occupati(client, chiamate):
    chiamate["risposte"] = [_risposta(429), _risposta(429)]
    r = client.post("/api/sommelier", json={"question": "cosa abbino a un risotto?"})
    assert r.status_code == 200
    dati = r.json()
    assert dati["demo_mode"] is True
    assert "occupati" in dati["answer"]


def test_rete_assente_risposta_dalle_regole(client, monkeypatch):
    def senza_rete(*args, **kwargs):
        raise requests.ConnectionError("Failed to resolve 'openrouter.ai'")

    monkeypatch.setattr(backend_main.requests, "post", senza_rete)
    r = client.post("/api/sommelier", json={"question": "cosa abbino a un risotto?"})
    assert r.status_code == 200
    assert r.json()["demo_mode"] is True
    assert "connessione" in r.json()["answer"]


def test_agente_sul_limite_risponde_503(client, chiamate):
    chiamate["risposte"] = [_risposta(429), _risposta(429)]
    r = client.post("/api/agente", json={"question": "quali rossi ho sotto i 15 euro?"})
    # 503 e non 502: l'interfaccia lo mostra come avviso, non come guasto.
    assert r.status_code == 503
    assert "occupati" in r.json()["detail"]
