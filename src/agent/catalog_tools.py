"""Strumenti che SVEVA puo' invocare sul catalogo (function calling).

DIFFERENZA RISPETTO AL RAG
--------------------------
Il RAG risponde a domande sul SAPERE enologico: e' conoscenza scritta,
statica, che sta in documenti indicizzati una volta sola. "Come si abbina un
piatto grasso" e' una domanda da RAG.

Il tool use risponde a domande sui DATI della cantina, che cambiano e sono
troppi per stare in un prompt: "quali rossi ho sopra 12 gradi sotto i 15
euro", "questo lotto regge la conservazione". Mettere 6.500 vini nel contesto
e' impossibile; farli descrivere a memoria dal modello sarebbe inventare.
Con il function calling il modello non conosce la risposta: chiede al
database, e noi eseguiamo la query.

CHI DECIDE COSA
---------------
Il modello sceglie QUALE strumento chiamare e con quali argomenti. Non scrive
SQL e non tocca il database: ogni strumento e' una funzione Python con
parametri tipizzati, e la query e' scritta qui, parametrizzata. Il modello
riempie dei buchi in un modulo che abbiamo definito noi.

Questa non e' una precauzione formale. Un modello che generasse SQL libero
potrebbe leggere tabelle che non lo riguardano o costruire query costose; e i
limiti (massimo 20 risultati, filtri consentiti) restano nostri anche quando
il modello chiede altro. Il modello propone, il codice dispone.
"""
from src.conservation import valuta_conservazione
from src.database.connection import DatabaseConnection

# Tetto ai risultati: il modello puo' chiederne di piu', non li ottiene.
# Serve a due cose insieme — non far esplodere i token del contesto e non
# permettere che una richiesta vaga si traduca in una scansione dell'intero
# catalogo.
MAX_RISULTATI = 20


def cerca_vini(
    tipo: str | None = None,
    qualita_minima: int | None = None,
    prezzo_massimo: float | None = None,
    alcol_minimo: float | None = None,
    alcol_massimo: float | None = None,
    limite: int = 5,
) -> list[dict]:
    """Cerca lotti nel catalogo per criteri numerici.

    Ogni filtro e' opzionale e viene aggiunto alla query solo se valorizzato:
    cosi' una domanda generica non impone vincoli inventati.
    """
    condizioni: list[str] = []
    parametri: list = []

    if tipo in ("red", "white"):
        condizioni.append("type = %s")
        parametri.append(tipo)
    if qualita_minima is not None:
        condizioni.append("quality >= %s")
        parametri.append(qualita_minima)
    if prezzo_massimo is not None:
        condizioni.append("price_eur <= %s")
        parametri.append(prezzo_massimo)
    if alcol_minimo is not None:
        condizioni.append("alcohol >= %s")
        parametri.append(alcol_minimo)
    if alcol_massimo is not None:
        condizioni.append("alcohol <= %s")
        parametri.append(alcol_massimo)

    where = f"WHERE {' AND '.join(condizioni)}" if condizioni else ""
    limite = max(1, min(int(limite or 5), MAX_RISULTATI))

    with DatabaseConnection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, type, quality, price_eur, alcohol, residual_sugar, "
            f"food_pairing FROM wines {where} "
            # Ordine per qualita': se il modello non specifica un criterio,
            # mostrare i lotti migliori e' il default piu' utile in cantina.
            f"ORDER BY quality DESC, price_eur ASC LIMIT {limite}",
            parametri,
        )
        righe = cursor.fetchall()
        cursor.close()

    return [
        {
            "id": r["id"],
            "nome": r["name"],
            "tipo": "rosso" if r["type"] == "red" else "bianco",
            "qualita": int(r["quality"]),
            "prezzo_eur": float(r["price_eur"]) if r["price_eur"] is not None else None,
            "alcol": float(r["alcohol"]),
            "zucchero_residuo": float(r["residual_sugar"]),
            "abbinamento": r["food_pairing"],
        }
        for r in righe
    ]


def scheda_lotto(wine_id: int) -> dict:
    """Restituisce chimica e stato di conservazione di un singolo lotto.

    La conservazione NON viene chiesta al modello: e' calcolata dalle regole
    in src/conservation.py (SO2 molecolare, acidita' volatile, pH, quota
    libera). Il modello riceve il verdetto gia' fatto e deve solo spiegarlo.
    Se lo calcolasse lui, sarebbe un'opinione travestita da misura.
    """
    with DatabaseConnection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, type, quality, price_eur, alcohol, ph, "
            "residual_sugar, fixed_acidity, volatile_acidity, sulphates, "
            "free_sulfur_dioxide, total_sulfur_dioxide, food_pairing "
            "FROM wines WHERE id = %s",
            (wine_id,),
        )
        w = cursor.fetchone()
        cursor.close()

    if w is None:
        # Errore restituito al modello come dato, non sollevato: cosi' puo'
        # correggersi da solo (ricercare, chiedere chiarimenti) invece di
        # far fallire l'intera conversazione.
        return {"errore": f"Nessun lotto con id {wine_id} nel catalogo."}

    cons = valuta_conservazione(
        wine_type=w["type"],
        free_sulfur_dioxide=float(w["free_sulfur_dioxide"]),
        total_sulfur_dioxide=float(w["total_sulfur_dioxide"]),
        ph=float(w["ph"]),
        volatile_acidity=float(w["volatile_acidity"]),
    )

    return {
        "id": w["id"],
        "nome": w["name"],
        "tipo": "rosso" if w["type"] == "red" else "bianco",
        "qualita": int(w["quality"]),
        "prezzo_eur": float(w["price_eur"]) if w["price_eur"] is not None else None,
        "alcol": float(w["alcohol"]),
        "ph": float(w["ph"]),
        "zucchero_residuo": float(w["residual_sugar"]),
        "acidita_fissa": float(w["fixed_acidity"]),
        "acidita_volatile": float(w["volatile_acidity"]),
        "solfati": float(w["sulphates"]),
        "abbinamento": w["food_pairing"],
        "conservazione": {
            "punteggio": cons.punteggio,
            "giudizio": cons.giudizio,
            "indicatori": [
                {"nome": i.nome, "livello": i.livello, "spiegazione": i.spiegazione}
                for i in cons.indicatori
            ],
        },
    }


# --------------------------------------------------------------------------
# Descrizioni per il modello.
#
# Sono l'unica cosa che il modello vede degli strumenti: la qualita' di
# queste frasi determina se sceglie lo strumento giusto. Vanno scritte come
# istruzioni per qualcuno che non conosce il database — quando usarlo, non
# solo cosa fa.
# --------------------------------------------------------------------------
STRUMENTI = [
    {
        "type": "function",
        "function": {
            "name": "cerca_vini",
            "description": (
                "Cerca lotti nel catalogo della cantina per criteri numerici "
                "(tipo, qualita', prezzo, gradazione). Usalo ogni volta che "
                "l'utente chiede QUALI vini ha, o ne chiede alcuni con certe "
                "caratteristiche. Non tirare mai a indovinare i lotti: non li "
                "conosci, devi cercarli."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {
                        "type": "string",
                        "enum": ["red", "white"],
                        "description": "red per i rossi, white per i bianchi",
                    },
                    "qualita_minima": {
                        "type": "integer",
                        "description": "punteggio di qualita' minimo, scala 0-10",
                    },
                    "prezzo_massimo": {"type": "number", "description": "prezzo in euro"},
                    "alcol_minimo": {"type": "number", "description": "gradi, es. 12.5"},
                    "alcol_massimo": {"type": "number", "description": "gradi, es. 13.5"},
                    "limite": {
                        "type": "integer",
                        "description": f"quanti risultati, massimo {MAX_RISULTATI}",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scheda_lotto",
            "description": (
                "Restituisce i dati completi di UN lotto: chimica e stato di "
                "conservazione gia' calcolato dal sistema. Usalo quando "
                "l'utente chiede dettagli su un vino specifico o se un lotto "
                "si conserva bene. Il giudizio di conservazione arriva da "
                "regole enologiche: riportalo, non ricalcolarlo a modo tuo. "
                "Se non conosci l'id del lotto, cercalo prima con cerca_vini."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "wine_id": {"type": "integer", "description": "id del lotto"},
                },
                "required": ["wine_id"],
            },
        },
    },
]

# Mappa nome -> funzione. Il modello puo' nominare solo queste: qualsiasi
# altro nome viene rifiutato dall'esecutore nel backend.
ESEGUIBILI = {
    "cerca_vini": cerca_vini,
    "scheda_lotto": scheda_lotto,
}
