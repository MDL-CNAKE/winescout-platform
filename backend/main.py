"""WineScout API - backend FastAPI.

Espone come endpoint REST tutta la logica gia' esistente in src/ (database,
modello ML, recommender, RAG): nessuna logica di dominio viene riscritta,
solo avvolta in un layer HTTP cosi' un frontend React puo' consumarla al
posto di Streamlit. Le regole di business (guardrail sul vitigno, brevita',
onesta' sull'abbinamento nel prompt del sommelier) restano identiche a
quelle validate nella versione Streamlit.
"""
import os
import re
import logging
from contextlib import asynccontextmanager

import joblib
import pandas as pd
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.database.connection import DatabaseConnection
from src.models.recommender import WineRecommender
from src.rag.retriever import KnowledgeRetriever

logger = logging.getLogger("winescout.api")

FEATURE_ORDER = [
    "type", "fixed_acidity", "volatile_acidity", "citric_acid", "residual_sugar",
    "chlorides", "free_sulfur_dioxide", "total_sulfur_dioxide", "density", "ph",
    "sulphates", "alcohol",
]

SYSTEM_PROMPT = (
    "Sei un sommelier esperto che parla con un collega o un cliente "
    "curioso. Rispondi in italiano dandogli del 'tu', in modo diretto e "
    "amichevole ma competente.\n\n"
    "TONO: niente formule di cortesia pompose ('Gentile ospite', 'Resto "
    "in attesa', 'La ringrazio per il contatto'). Niente linguaggio "
    "cerimonioso da lettera formale. Vai dritto al punto come farebbe un "
    "sommelier al banco: concreto, sicuro, senza giri di parole.\n\n"
    "LUNGHEZZA: massimo 2-3 frasi. Se la domanda e' vaga o mancano "
    "informazioni, NON scrivere un paragrafo per spiegarlo: chiedi in "
    "UNA frase cosa ti serve. Esempio di risposta corretta a una domanda "
    "poco chiara: 'Non ho capito quale piatto o quale vino ti interessa. "
    "Dimmi cosa stai mangiando o quale bottiglia hai in mente e ti do "
    "subito un consiglio.'\n\n"
    "TERMINOLOGIA: usa il gergo tecnico (esame visivo, olfattivo, "
    "gustativo, contrapposizione, concordanza) solo quando aggiunge "
    "davvero qualcosa alla risposta, mai come formula di rito.\n\n"
    "RICHIESTE NON COMPRENSIBILI: verifica sempre che il messaggio sia "
    "una domanda sensata su vino, abbinamenti o degustazione. Se contiene "
    "lettere a caso (es. 'kkkk', 'asdasd'), testo privo di senso o "
    "argomenti non pertinenti, IGNORA completamente i dati del vino "
    "selezionato e non produrre alcuna scheda o recensione: rispondi solo "
    "'Non ho capito la domanda. Chiedimi pure un consiglio o un "
    "abbinamento per questo vino.' Non inventare una domanda plausibile "
    "al posto dell'utente.\n\n"
    "IMPORTANTE: se ti viene fornita una 'Conoscenza enologica "
    "di riferimento', basa la risposta su quella invece che "
    "sulla tua memoria. Se l'utente nomina un piatto che non "
    "conosci, non rifiutare: scomponilo prima nelle sue "
    "sensazioni dominanti (grassezza, sapidita, tendenza amara, "
    "piccantezza, dolcezza, succulenza) e applica a quelle i "
    "principi di abbinamento. Questo vale per qualsiasi cucina "
    "del mondo, non solo europea.\n\n"
    "VINCOLO SUL VITIGNO: il nostro catalogo NON contiene "
    "l'informazione sul vitigno (uva) dei vini, solo tipo "
    "(rosso/bianco), profilo chimico, nome descrittivo, prezzo "
    "e abbinamento cibo. Se nel messaggio e' presente un vino "
    "specifico del catalogo (sezione 'Vino selezionato'), NON "
    "devi mai nominare o inventare un vitigno specifico per "
    "quel vino (es. non dire 'e' un Vermentino' o 'e' fatto con "
    "uve Sangiovese'): descrivilo solo con i dati reali forniti "
    "(tipo, gradazione, profilo chimico, note sensoriali "
    "plausibili derivate da quei dati). Puoi parlare di vitigni "
    "in termini generali SOLO se la domanda e' generica e non "
    "riguarda un vino specifico del catalogo.\n\n"
    "FORMATO: un unico paragrafo scorrevole. Niente tabelle, niente "
    "elenchi puntati, niente sezioni con titoli, a meno che l'utente non "
    "chieda esplicitamente un'analisi dettagliata punto per punto.\n\n"
    "ONESTA' SULL'ABBINAMENTO: non forzare un giudizio positivo "
    "solo perche' l'utente ha selezionato quel vino. Valuta "
    "onestamente quanto il vino scelto si adatta al piatto "
    "richiesto. Se l'abbinamento e' solo parziale o non "
    "ottimale, dillo chiaramente in una frase e specifica che "
    "tipo di profilo enologico (es. piu' struttura, piu' "
    "morbidezza, maggiore acidita', maggiore corpo) sarebbe "
    "piu' indicato, invece di razionalizzare a tutti i costi."
)

state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Carica modello, recommender e retriever una sola volta all'avvio
    (equivalente FastAPI di @st.cache_resource in Streamlit)."""
    state["model"] = joblib.load("models/quality_model.pkl")
    state["recommender"] = WineRecommender()
    try:
        state["retriever"] = KnowledgeRetriever()
    except Exception:
        state["retriever"] = None
        logger.warning("Indice RAG non disponibile: il sommelier funzionera' senza fonti verificate.")
    yield
    state.clear()


app = FastAPI(title="WineScout API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


class Wine(BaseModel):
    id: int
    name: str
    type: str
    alcohol: float
    ph: float
    residual_sugar: float
    fixed_acidity: float
    volatile_acidity: float
    chlorides: float
    sulphates: float
    quality: int
    price_eur: float | None
    margin_pct: float | None
    food_pairing: str | None


@app.get("/api/wines", response_model=list[Wine])
def get_wines():
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, name, type, alcohol, ph, residual_sugar, "
                "fixed_acidity, volatile_acidity, chlorides, sulphates, quality, "
                "price_eur, margin_pct, food_pairing FROM wines"
            )
            rows = cursor.fetchall()
            cursor.close()
            return rows
    except Exception as e:
        logger.exception("Errore nel caricamento del catalogo")
        raise HTTPException(status_code=500, detail="Errore nel caricamento del catalogo") from e


class PredictionInput(BaseModel):
    type: str
    fixed_acidity: float
    volatile_acidity: float
    citric_acid: float
    residual_sugar: float
    chlorides: float
    free_sulfur_dioxide: float
    total_sulfur_dioxide: float
    density: float
    ph: float
    sulphates: float
    alcohol: float


class PredictionOutput(BaseModel):
    quality: float


@app.post("/api/predict", response_model=PredictionOutput)
def predict(payload: PredictionInput):
    try:
        row = pd.DataFrame([payload.model_dump()])[FEATURE_ORDER]
        prediction = state["model"].predict(row)[0]
        return {"quality": round(float(prediction), 1)}
    except Exception as e:
        logger.exception("Errore nella predizione")
        raise HTTPException(status_code=500, detail="Errore nella predizione della qualita'") from e


class Recommendation(BaseModel):
    id: int
    name: str
    type: str
    alcohol: float
    ph: float
    quality: int
    price_eur: float
    similarity: float


class CheaperAlternative(Recommendation):
    savings_pct: float


@app.get("/api/recommend/{wine_id}", response_model=list[Recommendation])
def recommend(wine_id: int, top_n: int = 5):
    try:
        result = state["recommender"].recommend(wine_id=wine_id, top_n=top_n, same_type=True)
        return result.to_dict(orient="records")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.exception("Errore nella raccomandazione")
        raise HTTPException(status_code=500, detail="Errore nella raccomandazione") from e


@app.get("/api/recommend/{wine_id}/cheaper", response_model=list[CheaperAlternative])
def cheaper_alternative(wine_id: int):
    try:
        result = state["recommender"].find_cheaper_alternative(wine_id=wine_id)
        cols = ["id", "name", "type", "alcohol", "ph", "quality", "price_eur", "similarity", "savings_pct"]
        return result[cols].to_dict(orient="records")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.exception("Errore nella ricerca di alternative")
        raise HTTPException(status_code=500, detail="Errore nella ricerca di alternative") from e


class PackagingItem(BaseModel):
    id: int
    name: str
    type: str
    quality: int
    price_eur: float | None
    style: str
    bottle_format: str
    cap_type: str
    label_material: str


def _packaging_style(name: str, quality: int, price_eur: float | None) -> str:
    is_riserva = "Riserva" in name
    if is_riserva and quality >= 7:
        return "Elegante"
    if quality <= 4 or (price_eur is not None and price_eur < 13):
        return "Young"
    if quality >= 6:
        return "Classico"
    return "Moderno"


def _bottle_format(name: str, quality: int) -> str:
    if "Riserva" in name and quality >= 8:
        return "Magnum 1.5L"
    if quality <= 4:
        return "Mignon 375ml"
    return "Standard 750ml"


def _cap_type(wine_type: str, quality: int) -> str:
    if wine_type == "red" or quality >= 7:
        return "Tappo in sughero naturale"
    return "Tappo a vite"


def _label_material(style: str) -> str:
    return {
        "Elegante": "Carta pergamena con rilievo a caldo oro",
        "Classico": "Carta opaca con bordo inciso",
        "Moderno": "Carta patinata minimal",
        "Young": "Etichetta adesiva colorata",
    }[style]


@app.get("/api/packaging", response_model=list[PackagingItem])
def get_packaging():
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name, type, quality, price_eur FROM wines")
            rows = cursor.fetchall()
            cursor.close()
        result = []
        for w in rows:
            style = _packaging_style(w["name"], w["quality"], w["price_eur"])
            result.append({
                "id": w["id"],
                "name": w["name"],
                "type": w["type"],
                "quality": w["quality"],
                "price_eur": w["price_eur"],
                "style": style,
                "bottle_format": _bottle_format(w["name"], w["quality"]),
                "cap_type": _cap_type(w["type"], w["quality"]),
                "label_material": _label_material(style),
            })
        return result
    except Exception as e:
        logger.exception("Errore nel caricamento del packaging")
        raise HTTPException(status_code=500, detail="Errore nel caricamento del packaging") from e



NONSENSE_REPLY = (
    "Non ho capito la domanda. Chiedimi pure un consiglio o un abbinamento "
    "per questo vino."
)

_WORD_RE = re.compile(r"[a-zàèéìòùáíóúäëïöü]{2,}", re.IGNORECASE)
_VOWEL_RE = re.compile(r"[aeiouàèéìòùáíóúäëïöü]", re.IGNORECASE)


def is_meaningful_question(text: str) -> bool:
    """Filtro anti-gibberish: blocca 'kkkk', stringhe troppo corte o senza
    parole plausibili PRIMA di chiamare l'LLM.

    Senza questo controllo il modello, avendo in contesto i dati del vino
    selezionato, tende a "riempire il vuoto" generando comunque una scheda
    di degustazione anche quando l'utente non ha chiesto nulla di sensato.
    Non e' un'analisi linguistica completa (per quella servirebbe un
    modello), ma intercetta i casi piu' evidenti a costo zero.
    """
    clean = text.strip()
    if len(clean) < 8:
        return False

    compact = re.sub(r"\s+", "", clean)
    # Un solo carattere ripetuto: "kkkkkkkk", "aaaaaaaa".
    if len(set(compact.lower())) <= 2:
        return False

    words = _WORD_RE.findall(clean)
    if len(words) < 2:
        return False

    # Parole plausibili: contengono almeno una vocale e non sono una sola
    # lettera ripetuta.
    plausible = [
        w for w in words
        if _VOWEL_RE.search(w) and len(set(w.lower())) > 1
    ]
    return len(plausible) >= 2


class SommelierRequest(BaseModel):
    question: str
    wine_id: int | None = None


class SommelierResponse(BaseModel):
    answer: str
    demo_mode: bool
    sources: list[str] = []


@app.post("/api/sommelier", response_model=SommelierResponse)
def ask_sommelier(payload: SommelierRequest):
    # Guardia anti-gibberish: si risponde senza consumare una chiamata LLM
    # e senza mai passare al modello il contesto del vino, cosi' non puo'
    # generare una scheda di degustazione "a compensazione".
    if not is_meaningful_question(payload.question):
        return {"answer": NONSENSE_REPLY, "demo_mode": False, "sources": []}

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model_name = os.getenv("LLM_MODEL", "meta-llama/llama-3.1-8b-instruct")

    wine_context = ""
    wine_row = None
    if payload.wine_id is not None:
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT name, type, alcohol, quality, price_eur, food_pairing "
                    "FROM wines WHERE id = %s",
                    (payload.wine_id,),
                )
                wine_row = cursor.fetchone()
                cursor.close()
        except Exception as e:
            logger.exception("Errore nel recupero del vino di contesto")
            raise HTTPException(status_code=500, detail="Errore nel recupero del vino") from e

        if wine_row is None:
            raise HTTPException(status_code=404, detail=f"Vino con id={payload.wine_id} non trovato")

        wine_context = (
            f"\n\nContesto dal database (usa questi dati reali nella risposta): "
            f"vino '{wine_row['name']}', tipo {wine_row['type']}, alcol {wine_row['alcohol']}%, "
            f"qualità {int(wine_row['quality'])}/10, prezzo {wine_row['price_eur']} EUR. "
            f"Abbinamento suggerito dal sistema: {wine_row['food_pairing']}."
        )

    retriever = state.get("retriever")
    rag_context = ""
    sources: list[str] = []
    if retriever is not None and payload.question.strip():
        retrieved = retriever.search(payload.question, top_k=3)
        sources = retrieved
        if retrieved:
            rag_context = "\n\n" + retriever.build_context(payload.question, top_k=3)

    if not api_key or api_key == "metti_qui_la_tua_chiave":
        if wine_row is not None:
            answer = (
                f"Per {wine_row['name']} ({wine_row['type']}, {wine_row['alcohol']}% vol, "
                f"qualità {int(wine_row['quality'])}/10) il nostro sistema suggerisce questo "
                f"abbinamento: {wine_row['food_pairing']}. "
                "(Risposta generata dalle regole del sistema. Configura OPENROUTER_API_KEY "
                "nel file .env per una descrizione elaborata dall'LLM.)"
            )
        else:
            answer = (
                "Seleziona un vino del catalogo per vedere un abbinamento reale, oppure "
                "configura OPENROUTER_API_KEY nel file .env per risposte elaborate dall'IA."
            )
        return {"answer": answer, "demo_mode": True, "sources": sources}

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_name,
                "max_tokens": 1500,
                "reasoning": {"effort": "low"},
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": payload.question + wine_context + rag_context},
                ],
            },
            timeout=60,
        )
        response.raise_for_status()
        answer = response.json()["choices"][0]["message"]["content"]
        return {"answer": answer, "demo_mode": False, "sources": sources}
    except Exception as e:
        logger.exception("Errore nella chiamata all'LLM")
        raise HTTPException(status_code=502, detail=f"Errore nella chiamata al Sommelier: {e}") from e
