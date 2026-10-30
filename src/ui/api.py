"""Client HTTP verso il backend FastAPI.

PERCHE' STREAMLIT CHIAMA L'API E NON IMPORTA src/ DIRETTAMENTE
--------------------------------------------------------------
La logica di SVEVA (prompt, filtro anti-gibberish, ciclo dell'agente,
finestra della memoria, verdetto validato) vive in backend/main.py ed e'
coperta dai test. Reimportarla qui significherebbe averne due copie, e due
copie della stessa regola divergono appena una delle due cambia: e' gia'
successo nel progetto con lo split di train.py e importance.py.

Cosi' Streamlit e React sono due interfacce sullo stesso backend: mostrano
gli stessi numeri perche' li chiedono alla stessa fonte.

CACHE
-----
Le letture sono in cache con una durata breve: Streamlit riesegue lo script
a ogni interazione, e senza cache ogni click rifarebbe tutte le richieste
della pagina. Le scritture (preferiti, profili, operatori) svuotano la cache
delle letture che modificano.
"""
import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")

# Letture e scritture semplici: il backend risponde in pochi decimi di secondo.
TIMEOUT = 15
# Le chiamate a un LLM sono piu' lente. Il backend usa 60 s per singola
# chiamata e ne fa al massimo due (verdetto) o quattro (agente).
TIMEOUT_LLM = 150
TIMEOUT_AGENTE = 260


class ApiError(Exception):
    """Errore del backend, con il messaggio leggibile che il backend fornisce."""

    def __init__(self, messaggio: str, stato: int | None = None) -> None:
        super().__init__(messaggio)
        self.stato = stato


def richiesta(metodo: str, percorso: str, *, params: dict | None = None,
              payload: dict | None = None, timeout: float = TIMEOUT,
              grezzo: bool = False):
    """Esegue una richiesta e restituisce il JSON (o i byte se `grezzo`).

    Gli errori arrivano all'interfaccia come ApiError con il campo `detail`
    del backend: e' gia' scritto per chi usa l'applicazione ("Vino con id=5
    non trovato"), non serve riformularlo.
    """
    url = f"{BACKEND_URL}{percorso}"
    try:
        risposta = requests.request(metodo, url, params=params, json=payload, timeout=timeout)
    except requests.Timeout as e:
        raise ApiError("Il backend non ha risposto in tempo. Riprova.") from e
    except requests.ConnectionError as e:
        raise ApiError(
            f"Backend non raggiungibile su {BACKEND_URL}. "
            "Avvialo con 'docker compose up backend'."
        ) from e

    if risposta.status_code >= 400:
        try:
            dettaglio = risposta.json().get("detail")
        except ValueError:
            dettaglio = None
        raise ApiError(dettaglio or f"Errore {risposta.status_code} dal backend",
                       risposta.status_code)

    if grezzo:
        return risposta.content
    if risposta.status_code == 204 or not risposta.content:
        return None
    return risposta.json()


# --------------------------------------------------------------------------
# Letture (in cache)
# --------------------------------------------------------------------------

@st.cache_data(ttl=10, show_spinner=False)
def backend_attivo() -> bool:
    try:
        richiesta("GET", "/api/health", timeout=3)
        return True
    except ApiError:
        return False


@st.cache_data(ttl=600, show_spinner=False)
def vini_sommario() -> list[dict]:
    return richiesta("GET", "/api/wines/summary")


@st.cache_data(ttl=600, show_spinner=False)
def intervalli() -> dict:
    return richiesta("GET", "/api/wines/facets")


@st.cache_data(ttl=120, show_spinner=False)
def cerca_vini(filtri: dict, ordine: str, pagina: int, per_pagina: int) -> dict:
    params = {**filtri, "sort": ordine, "page": pagina, "page_size": per_pagina}
    return richiesta("GET", "/api/wines/search", params=params)


@st.cache_data(ttl=600, show_spinner=False)
def vino(wine_id: int) -> dict:
    return richiesta("GET", f"/api/wines/{wine_id}")


@st.cache_data(ttl=600, show_spinner=False)
def raccomandazioni(wine_id: int) -> list[dict]:
    return richiesta("GET", f"/api/recommend/{wine_id}")


@st.cache_data(ttl=600, show_spinner=False)
def alternative_economiche(wine_id: int) -> list[dict]:
    return richiesta("GET", f"/api/recommend/{wine_id}/cheaper")


@st.cache_data(ttl=600, show_spinner=False)
def packaging_lista() -> list[dict]:
    return richiesta("GET", "/api/packaging")


@st.cache_data(ttl=600, show_spinner=False)
def packaging(wine_id: int) -> dict:
    return richiesta("GET", f"/api/packaging/{wine_id}")


@st.cache_data(ttl=600, show_spinner=False)
def conservazione_lista(tipo: str | None, limite: int) -> list[dict]:
    return richiesta("GET", "/api/conservazione", params={"type": tipo, "limit": limite})


@st.cache_data(ttl=600, show_spinner=False)
def conservazione(wine_id: int) -> dict:
    return richiesta("GET", f"/api/conservazione/{wine_id}")


@st.cache_data(ttl=600, show_spinner=False)
def leve(wine_id: int) -> dict:
    return richiesta("GET", f"/api/leve/{wine_id}")


@st.cache_data(ttl=3600, show_spinner=False)
def importanza() -> list[dict]:
    # Il primo calcolo richiede qualche secondo; finche' il modello resta lo
    # stesso il risultato non cambia.
    return richiesta("GET", "/api/importanza", timeout=120)


@st.cache_data(ttl=60, show_spinner=False)
def operatori() -> list[dict]:
    return richiesta("GET", "/api/operators")


@st.cache_data(ttl=15, show_spinner=False)
def preferiti() -> list[dict]:
    return richiesta("GET", "/api/favorites")


@st.cache_data(ttl=30, show_spinner=False)
def profili() -> list[dict]:
    return richiesta("GET", "/api/profili")


@st.cache_data(ttl=30, show_spinner=False)
def vini_per_profilo(profile_id: int) -> list[dict]:
    return richiesta("GET", f"/api/profili/{profile_id}/vini")


# --------------------------------------------------------------------------
# Scritture e chiamate al modello (mai in cache)
# --------------------------------------------------------------------------

def esporta_csv(filtri: dict, ordine: str, formato: str) -> bytes:
    params = {**filtri, "sort": ordine, "formato": formato}
    return richiesta("GET", "/api/wines/export.csv", params=params, timeout=60, grezzo=True)


def crea_operatore(nome: str, ruolo: str) -> dict:
    nuovo = richiesta("POST", "/api/operators", payload={"name": nome, "role": ruolo})
    operatori.clear()
    return nuovo


def aggiungi_preferito(wine_id: int, operator_id: int) -> None:
    richiesta("POST", "/api/favorites", payload={"wine_id": wine_id, "operator_id": operator_id})
    preferiti.clear()


def rimuovi_preferito(wine_id: int, operator_id: int) -> None:
    richiesta("DELETE", "/api/favorites", params={"wine_id": wine_id, "operator_id": operator_id})
    preferiti.clear()


def crea_profilo(dati: dict) -> dict:
    nuovo = richiesta("POST", "/api/profili", payload=dati)
    profili.clear()
    return nuovo


def elimina_profilo(profile_id: int) -> None:
    richiesta("DELETE", f"/api/profili/{profile_id}")
    profili.clear()
    vini_per_profilo.clear()


def predici(valori: dict) -> float:
    return richiesta("POST", "/api/predict", payload=valori)["quality"]


def chiedi_sommelier(domanda: str, wine_id: int | None, storico: list[dict]) -> dict:
    """Lo storico parte dal client a ogni domanda: il backend resta senza
    stato, e decide lui quanta parte usarne (finestra scorrevole)."""
    payload = {"question": domanda, "wine_id": wine_id, "storico": list(storico)}
    return richiesta("POST", "/api/sommelier", payload=payload, timeout=TIMEOUT_LLM)


def chiedi_agente(domanda: str) -> dict:
    return richiesta("POST", "/api/agente", payload={"question": domanda}, timeout=TIMEOUT_AGENTE)


def verdetto(wine_id: int, piatto: str) -> dict:
    return richiesta("POST", "/api/verdetto", payload={"wine_id": wine_id, "piatto": piatto},
                     timeout=TIMEOUT_LLM)
