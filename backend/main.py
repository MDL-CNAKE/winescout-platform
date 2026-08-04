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
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel

from src.conservation import valuta_conservazione
from src.levers import analizza_leve
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
    "Ti chiami SVEVA (Sommelier Virtuale Esperta in Vini e Abbinamenti). "
    "Sei una sommelier esperta che parla con un collega o un cliente "
    "curioso. Rispondi in italiano dandogli del 'tu', in modo diretto e "
    "amichevole ma competente.\n\n"
    "NON sei un'enologa: quello e' un titolo professionale che richiede "
    "una laurea e l'iscrizione all'albo. Se ti viene chiesto, dillo "
    "chiaramente: sei un assistente che ragiona sui dati chimici del "
    "catalogo e sui principi di abbinamento, non un professionista "
    "abilitato, e per decisioni tecniche di cantina serve un enologo "
    "vero.\n\n"
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
    "ANCORAGGIO AI DATI: quando parli di un vino del catalogo, giustifica "
    "il consiglio citando UN dato reale fra quelli che ti sono stati "
    "forniti (gradazione alcolica, pH, acidita', zucchero residuo, "
    "solfati, qualita'), integrato nella frase e non come elenco. Cita un "
    "solo dato, quello piu' pertinente alla domanda: l'obiettivo e' "
    "ancorare il consiglio, non fare una scheda analitica. Non menzionare "
    "MAI caratteristiche assenti dai dati: il dataset non contiene "
    "tannini, annata, terroir, affinamento, note aromatiche o vitigno, "
    "quindi non puoi citarli come se li conoscessi.\n\n"
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

# Compressione delle risposte: /api/wines restituisce 6497 record con tutte
# le colonne, circa 2 MB di JSON. E' testo molto ripetitivo (nomi di campo e
# stringhe di abbinamento identiche su migliaia di righe), quindi comprime
# di circa dieci volte. La soglia evita di sprecare CPU sulle risposte
# piccole, dove il guadagno sarebbe nullo.
app.add_middleware(GZipMiddleware, minimum_size=1000)


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


class WineSummary(BaseModel):
    id: int
    name: str
    type: str


# ATTENZIONE all'ordine: questa rotta deve precedere /api/wines/{wine_id},
# altrimenti FastAPI proverebbe a interpretare "summary" come intero e
# risponderebbe 422.
@app.get("/api/wines/summary", response_model=list[WineSummary])
def get_wines_summary():
    """Elenco leggero (id, nome, tipo) per le liste di navigazione.

    La sidebar della scheda vino mostra solo i nomi: scaricare anche le
    undici colonne chimiche di 6497 record sarebbe sproporzionato.
    """
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name, type FROM wines")
            rows = cursor.fetchall()
            cursor.close()
            return rows
    except Exception as e:
        logger.exception("Errore nel caricamento dell'elenco vini")
        raise HTTPException(status_code=500, detail="Errore nel caricamento dell'elenco") from e


class WineFacets(BaseModel):
    """Estremi reali del catalogo, per tarare i cursori dei filtri sui dati
    invece che su valori inventati nel frontend."""
    alcohol: tuple[float, float]
    residual_sugar: tuple[float, float]
    fixed_acidity: tuple[float, float]
    price_eur: tuple[float, float]
    quality: tuple[int, int]


@app.get("/api/wines/facets", response_model=WineFacets)
def get_wine_facets():
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT MIN(alcohol), MAX(alcohol), MIN(residual_sugar), "
                "MAX(residual_sugar), MIN(fixed_acidity), MAX(fixed_acidity), "
                "MIN(price_eur), MAX(price_eur), MIN(quality), MAX(quality) "
                "FROM wines"
            )
            r = cursor.fetchone()
            cursor.close()
        return {
            "alcohol": (float(r[0]), float(r[1])),
            "residual_sugar": (float(r[2]), float(r[3])),
            "fixed_acidity": (float(r[4]), float(r[5])),
            "price_eur": (float(r[6]), float(r[7])),
            "quality": (int(r[8]), int(r[9])),
        }
    except Exception as e:
        logger.exception("Errore nel calcolo degli intervalli")
        raise HTTPException(status_code=500, detail="Errore nel calcolo degli intervalli") from e


class WineSearchResult(BaseModel):
    items: list[Wine]
    total: int
    page: int
    page_size: int


# Ordinamenti ammessi: la clausola ORDER BY non puo' essere parametrizzata,
# quindi si accetta solo una chiave da questa mappa. Mai concatenare in SQL
# una stringa che arriva dal client.
SORT_OPTIONS = {
    "price_asc": "price_eur ASC",
    "price_desc": "price_eur DESC",
    "quality_desc": "quality DESC, price_eur ASC",
    "quality_asc": "quality ASC, price_eur ASC",
    "alcohol_desc": "alcohol DESC",
    "name_asc": "name ASC",
}

MAX_PAGE_SIZE = 60


@app.get("/api/wines/search", response_model=WineSearchResult)
def search_wines(
    type: str | None = None,
    min_quality: int | None = None,
    min_alcohol: float | None = None,
    max_alcohol: float | None = None,
    min_sugar: float | None = None,
    max_sugar: float | None = None,
    min_acidity: float | None = None,
    max_acidity: float | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    sort: str = "quality_desc",
    page: int = 1,
    page_size: int = 24,
):
    """Catalogo filtrato, ordinato e paginato.

    Filtri e ordinamento avvengono in SQL, non nel browser: con 6497 record
    scaricare tutto per mostrarne 24 sarebbe uno spreco, e la griglia della
    home ne mostra comunque una pagina alla volta.
    """
    if sort not in SORT_OPTIONS:
        raise HTTPException(status_code=400, detail=f"Ordinamento non valido: {sort}")
    if type is not None and type not in ("red", "white"):
        raise HTTPException(status_code=400, detail="Tipo non valido: usare 'red' o 'white'")

    page = max(1, page)
    page_size = max(1, min(page_size, MAX_PAGE_SIZE))

    conditions: list[str] = []
    params: list = []

    def add(clause: str, value) -> None:
        if value is not None:
            conditions.append(clause)
            params.append(value)

    add("type = %s", type)
    add("quality >= %s", min_quality)
    add("alcohol >= %s", min_alcohol)
    add("alcohol <= %s", max_alcohol)
    add("residual_sugar >= %s", min_sugar)
    add("residual_sugar <= %s", max_sugar)
    add("fixed_acidity >= %s", min_acidity)
    add("fixed_acidity <= %s", max_acidity)
    add("price_eur >= %s", min_price)
    add("price_eur <= %s", max_price)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute(f"SELECT COUNT(*) AS n FROM wines {where}", params)
            total = cursor.fetchone()["n"]

            cursor.execute(
                "SELECT id, name, type, alcohol, ph, residual_sugar, "
                "fixed_acidity, volatile_acidity, chlorides, sulphates, quality, "
                f"price_eur, margin_pct, food_pairing FROM wines {where} "
                f"ORDER BY {SORT_OPTIONS[sort]}, id ASC LIMIT %s OFFSET %s",
                params + [page_size, (page - 1) * page_size],
            )
            items = cursor.fetchall()
            cursor.close()

        return {"items": items, "total": total, "page": page, "page_size": page_size}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Errore nella ricerca del catalogo")
        raise HTTPException(status_code=500, detail="Errore nella ricerca del catalogo") from e


@app.get("/api/wines/{wine_id}", response_model=Wine)
def get_wine(wine_id: int):
    """Singolo vino: evita di scaricare l'intero catalogo per usarne uno."""
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, name, type, alcohol, ph, residual_sugar, "
                "fixed_acidity, volatile_acidity, chlorides, sulphates, quality, "
                "price_eur, margin_pct, food_pairing FROM wines WHERE id = %s",
                (wine_id,),
            )
            row = cursor.fetchone()
            cursor.close()
    except Exception as e:
        logger.exception("Errore nel caricamento del vino")
        raise HTTPException(status_code=500, detail="Errore nel caricamento del vino") from e

    if row is None:
        raise HTTPException(status_code=404, detail=f"Vino con id={wine_id} non trovato")
    return row


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
    """Il criterio si basa su qualita' e prezzo, non sulla menzione
    'Riserva': quella indica per legge un affinamento minimo di cui il
    dataset non ha traccia, ed e' stata rimossa dai nomi."""
    del name  # mantenuto nella firma per compatibilita' con i chiamanti
    if quality >= 7:
        return "Elegante"
    if quality <= 4 or (price_eur is not None and price_eur < 13):
        return "Young"
    if quality >= 6:
        return "Classico"
    return "Moderno"


def _bottle_format(name: str, quality: int) -> str:
    del name
    if quality >= 8:
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


@app.get("/api/packaging/{wine_id}", response_model=PackagingItem)
def get_packaging_item(wine_id: int):
    """Scheda packaging di un singolo vino, senza scaricare l'intera lista."""
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, name, type, quality, price_eur FROM wines WHERE id = %s",
                (wine_id,),
            )
            w = cursor.fetchone()
            cursor.close()
    except Exception as e:
        logger.exception("Errore nel caricamento del packaging")
        raise HTTPException(status_code=500, detail="Errore nel caricamento del packaging") from e

    if w is None:
        raise HTTPException(status_code=404, detail=f"Vino con id={wine_id} non trovato")

    style = _packaging_style(w["name"], w["quality"], w["price_eur"])
    return {
        "id": w["id"],
        "name": w["name"],
        "type": w["type"],
        "quality": w["quality"],
        "price_eur": w["price_eur"],
        "style": style,
        "bottle_format": _bottle_format(w["name"], w["quality"]),
        "cap_type": _cap_type(w["type"], w["quality"]),
        "label_material": _label_material(style),
    }


# --------------------------------------------------------------------------
# Selezioni di lavoro condivise
#
# Non c'e' autenticazione: l'applicazione appartiene a una sola cantina e chi
# la usa si dichiara scegliendo il proprio nome dall'elenco degli operatori.
# Le preferenze restano quindi distinte per persona pur vivendo in un'unica
# tabella condivisa, cosi' un collega vede cosa ha segnato l'altro.
# --------------------------------------------------------------------------

class Operator(BaseModel):
    id: int
    name: str


class OperatorCreate(BaseModel):
    name: str


class Favorite(BaseModel):
    wine_id: int
    operator_id: int
    operator_name: str


class FavoriteRequest(BaseModel):
    wine_id: int
    operator_id: int


@app.get("/api/operators", response_model=list[Operator])
def get_operators():
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name FROM operators ORDER BY name")
            rows = cursor.fetchall()
            cursor.close()
            return rows
    except Exception as e:
        logger.exception("Errore nel caricamento degli operatori")
        raise HTTPException(status_code=500, detail="Errore nel caricamento degli operatori") from e


@app.post("/api/operators", response_model=Operator, status_code=201)
def create_operator(payload: OperatorCreate):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Il nome non puo' essere vuoto")
    if len(name) > 60:
        raise HTTPException(status_code=400, detail="Nome troppo lungo (max 60 caratteri)")

    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO operators (name) VALUES (%s)", (name,))
            new_id = cursor.lastrowid
            conn.commit()
            cursor.close()
        return {"id": new_id, "name": name}
    except Exception as e:
        # Il vincolo di unicita' sul nome e' la causa piu' probabile.
        logger.exception("Errore nella creazione dell'operatore")
        raise HTTPException(status_code=409, detail="Operatore gia' esistente o non valido") from e


@app.get("/api/favorites", response_model=list[Favorite])
def get_favorites():
    """Tutte le selezioni con il nome di chi le ha fatte.

    Si restituisce l'elenco completo perche' e' piccolo (poche decine di
    righe per cantina) e serve alla griglia per mostrare su ogni card chi
    altro ha segnato quel vino.
    """
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT f.wine_id, f.operator_id, o.name AS operator_name "
                "FROM favorites f JOIN operators o ON o.id = f.operator_id"
            )
            rows = cursor.fetchall()
            cursor.close()
            return rows
    except Exception as e:
        logger.exception("Errore nel caricamento delle selezioni")
        raise HTTPException(status_code=500, detail="Errore nel caricamento delle selezioni") from e


@app.post("/api/favorites", status_code=204)
def add_favorite(payload: FavoriteRequest):
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            # Ripetere l'inserimento non e' un errore: l'operazione e'
            # idempotente, cosi' un doppio click non genera un 500.
            cursor.execute(
                "INSERT IGNORE INTO favorites (wine_id, operator_id) VALUES (%s, %s)",
                (payload.wine_id, payload.operator_id),
            )
            conn.commit()
            cursor.close()
    except Exception as e:
        logger.exception("Errore nel salvataggio della selezione")
        raise HTTPException(status_code=500, detail="Errore nel salvataggio della selezione") from e


@app.delete("/api/favorites", status_code=204)
def remove_favorite(wine_id: int, operator_id: int):
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM favorites WHERE wine_id = %s AND operator_id = %s",
                (wine_id, operator_id),
            )
            conn.commit()
            cursor.close()
    except Exception as e:
        logger.exception("Errore nella rimozione della selezione")
        raise HTTPException(status_code=500, detail="Errore nella rimozione della selezione") from e


# --------------------------------------------------------------------------
# Predisposizione alla conservazione
#
# Indice a REGOLE, non modello addestrato: il dataset non contiene etichette
# sull'evoluzione dei vini nel tempo, quindi non esiste una verita' di
# riferimento su cui addestrare. Vedi src/conservation.py per la
# motivazione enologica di ciascun indicatore.
# --------------------------------------------------------------------------

class IndicatoreOut(BaseModel):
    nome: str
    valore: float
    unita: str
    livello: str
    spiegazione: str


class ConservazioneOut(BaseModel):
    id: int
    name: str
    type: str
    quality: int
    price_eur: float | None
    punteggio: int
    giudizio: str
    indicatori: list[IndicatoreOut]


class ConservazioneRiga(BaseModel):
    """Riga sintetica per la vista d'insieme del magazzino."""
    id: int
    name: str
    type: str
    quality: int
    price_eur: float | None
    punteggio: int
    giudizio: str


_CONS_COLS = (
    "id, name, type, quality, price_eur, free_sulfur_dioxide, "
    "total_sulfur_dioxide, ph, volatile_acidity"
)


def _conservazione_da_riga(w: dict):
    return valuta_conservazione(
        wine_type=w["type"],
        free_sulfur_dioxide=float(w["free_sulfur_dioxide"]),
        total_sulfur_dioxide=float(w["total_sulfur_dioxide"]),
        ph=float(w["ph"]),
        volatile_acidity=float(w["volatile_acidity"]),
    )


@app.get("/api/conservazione", response_model=list[ConservazioneRiga])
def lista_conservazione(type: str | None = None, limit: int = 60):
    """Catalogo ordinato per rischio: i lotti da muovere per primi in cima.

    L'ordinamento avviene in Python e non in SQL perche' il punteggio non e'
    una colonna del database ma il risultato delle regole enologiche: e' un
    valore derivato, e replicarlo in SQL significherebbe duplicare la logica
    in due posti che poi divergono.
    """
    if type is not None and type not in ("red", "white"):
        raise HTTPException(status_code=400, detail="Tipo non valido")
    limit = max(1, min(limit, 200))

    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor(dictionary=True)
            where = "WHERE type = %s" if type else ""
            cursor.execute(
                f"SELECT {_CONS_COLS} FROM wines {where}",
                (type,) if type else (),
            )
            rows = cursor.fetchall()
            cursor.close()
    except Exception as e:
        logger.exception("Errore nel calcolo della conservazione")
        raise HTTPException(status_code=500, detail="Errore nel calcolo della conservazione") from e

    out = []
    for w in rows:
        c = _conservazione_da_riga(w)
        out.append({
            "id": w["id"], "name": w["name"], "type": w["type"],
            "quality": w["quality"], "price_eur": w["price_eur"],
            "punteggio": c.punteggio, "giudizio": c.giudizio,
        })

    out.sort(key=lambda r: (r["punteggio"], -r["quality"]))
    return out[:limit]


@app.get("/api/conservazione/{wine_id}", response_model=ConservazioneOut)
def conservazione_vino(wine_id: int):
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(f"SELECT {_CONS_COLS} FROM wines WHERE id = %s", (wine_id,))
            w = cursor.fetchone()
            cursor.close()
    except Exception as e:
        logger.exception("Errore nel calcolo della conservazione")
        raise HTTPException(status_code=500, detail="Errore nel calcolo della conservazione") from e

    if w is None:
        raise HTTPException(status_code=404, detail=f"Vino con id={wine_id} non trovato")

    c = _conservazione_da_riga(w)
    return {
        "id": w["id"], "name": w["name"], "type": w["type"],
        "quality": w["quality"], "price_eur": w["price_eur"],
        "punteggio": c.punteggio, "giudizio": c.giudizio,
        "indicatori": [vars(i) for i in c.indicatori],
    }


# --------------------------------------------------------------------------
# Leve di miglioramento
#
# Analisi controfattuale a un parametro alla volta sul modello addestrato:
# quale correzione conviene applicare a questo lotto e quanto rende. Vedi
# src/levers.py per i passi scelti e per i limiti dell'approccio.
# --------------------------------------------------------------------------

class EffettoLevaOut(BaseModel):
    campo: str
    etichetta: str
    unita: str
    valore_attuale: float
    valore_proposto: float
    variazione: float
    delta_qualita: float
    direzione: str
    intervento: str


class LeveOut(BaseModel):
    id: int
    name: str
    qualita_reale: int
    previsione_attuale: float
    leve: list[EffettoLevaOut]


@app.get("/api/leve/{wine_id}", response_model=LeveOut)
def leve_di_miglioramento(wine_id: int):
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, name, type, quality, fixed_acidity, volatile_acidity, "
                "citric_acid, residual_sugar, chlorides, free_sulfur_dioxide, "
                "total_sulfur_dioxide, density, ph, sulphates, alcohol "
                "FROM wines WHERE id = %s",
                (wine_id,),
            )
            w = cursor.fetchone()
            cursor.close()
    except Exception as e:
        logger.exception("Errore nel recupero del vino")
        raise HTTPException(status_code=500, detail="Errore nel recupero del vino") from e

    if w is None:
        raise HTTPException(status_code=404, detail=f"Vino con id={wine_id} non trovato")

    try:
        wine = {k: (float(v) if k not in ("id", "name", "type", "quality") else v)
                for k, v in w.items()}
        base, leve = analizza_leve(state["model"], wine)
    except Exception as e:
        logger.exception("Errore nel calcolo delle leve")
        raise HTTPException(status_code=500, detail="Errore nel calcolo delle leve") from e

    return {
        "id": w["id"],
        "name": w["name"],
        "qualita_reale": w["quality"],
        "previsione_attuale": base,
        "leve": [vars(e) for e in leve],
    }


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
