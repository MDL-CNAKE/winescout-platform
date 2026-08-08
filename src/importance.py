"""Cosa guida la qualita' secondo il modello: importanza per permutazione.

PERCHE' LA PERMUTAZIONE E NON feature_importances_
---------------------------------------------------
RandomForest espone `feature_importances_`, basata sulla riduzione di impurita'
negli alberi. E' gratuita ma ha un difetto noto: **sovrastima le variabili con
molti valori distinti**, perche' offrono piu' punti di taglio. Su dati come
questi, dove le misure di laboratorio hanno moltissimi valori diversi, il
risultato sarebbe distorto.

L'importanza per permutazione misura un'altra cosa, piu' vicina alla domanda
reale: si mescolano a caso i valori di una colonna e si osserva **quanto
peggiora la previsione**. Se rompere una variabile non peggiora nulla, quella
variabile non serviva.

PERCHE' SI CALCOLA SUL TEST SET
--------------------------------
Calcolata sui dati di addestramento, l'importanza dice cosa il modello ha
*usato*; calcolata su dati mai visti, dice cosa **generalizza**. La seconda e'
l'unica utile a chi deve prendere decisioni. La suddivisione replica quella di
src/models/train.py (80/20, seed 42, stratificata per tipo) in modo che il
test set sia davvero lo stesso su cui il modello e' stato valutato.

COSTO E CACHE
-------------
Il calcolo richiede alcune decine di valutazioni del modello: si esegue una
volta sola alla prima richiesta e si tiene in memoria, invece di appesantire
l'avvio del servizio, gia' occupato dal caricamento del modello e dell'indice RAG.
"""
from dataclasses import dataclass

import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split

NUM = [
    "fixed_acidity", "volatile_acidity", "citric_acid", "residual_sugar",
    "chlorides", "free_sulfur_dioxide", "total_sulfur_dioxide",
    "density", "ph", "sulphates", "alcohol",
]

# Lettura enologica di ciascuna variabile: il numero da solo non dice a una
# cantina perche' quel parametro conti.
SIGNIFICATO = {
    "alcohol": (
        "Grado alcolico",
        "Proxy della maturazione dell'uva e del corpo del vino: nel dataset e' "
        "il segnale piu' forte di qualita' percepita.",
    ),
    "volatile_acidity": (
        "Acidità volatile",
        "Marcatore di deterioramento (spunto acetico). Pesa in negativo: piu' "
        "e' alta, piu' il giudizio scende.",
    ),
    "free_sulfur_dioxide": (
        "SO2 libera",
        "Protezione da ossidazione e rifermentazione. Conta in entrambe le "
        "direzioni: troppo poca espone il vino, troppa si sente al naso.",
    ),
    "sulphates": (
        "Solfati",
        "Legati alla stabilita' microbiologica e alla percezione dell'amaro.",
    ),
    "total_sulfur_dioxide": (
        "SO2 totale",
        "Somma di libera e legata. Valori elevati indicano un vino molto "
        "protetto, a volte a scapito della finezza.",
    ),
    "residual_sugar": (
        "Zucchero residuo",
        "Equilibrio gustativo: incide sulla percezione di morbidezza.",
    ),
    "ph": (
        "pH",
        "Acidita' percepita e conservabilita'. Governa anche l'efficacia della "
        "solforosa.",
    ),
    "citric_acid": (
        "Acido citrico",
        "Contributo alla freschezza, presente in quantita' minori rispetto agli "
        "altri acidi.",
    ),
    "chlorides": (
        "Cloruri",
        "Salinita' del vino, legata all'acqua di processo e al terreno.",
    ),
    "density": (
        "Densità",
        "Dipende da alcol e zuccheri: porta in gran parte informazione gia' "
        "contenuta in quelle due variabili.",
    ),
    "fixed_acidity": (
        "Acidità fissa",
        "Struttura acida stabile del vino, prevalentemente acido tartarico.",
    ),
    "type": (
        "Tipo (rosso/bianco)",
        "Nota il valore prossimo allo zero: una volta noto il profilo chimico, "
        "sapere se il vino e' rosso o bianco non aggiunge nulla alla previsione.",
    ),
}


@dataclass
class VariabileImportanza:
    campo: str
    etichetta: str
    importanza: float       # calo di R2 quando la variabile viene mescolata
    incertezza: float       # deviazione standard fra le ripetizioni
    quota: float            # peso relativo in percentuale
    significato: str


_cache: list[VariabileImportanza] | None = None


def calcola_importanza(model, df: pd.DataFrame, n_repeats: int = 5) -> list[VariabileImportanza]:
    """Importanza per permutazione sul test set, ordinata per rilevanza."""
    global _cache
    if _cache is not None:
        return _cache

    X = df[["type"] + NUM]
    y = df["quality"]
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=df["type"]
    )

    res = permutation_importance(
        model, X_test, y_test, n_repeats=n_repeats, random_state=42, scoring="r2"
    )

    # I contributi negativi sono rumore (mescolare la variabile ha per caso
    # migliorato la previsione): si azzerano per il calcolo delle quote, ma il
    # valore grezzo resta visibile.
    totale = sum(max(0.0, v) for v in res.importances_mean) or 1.0

    out = []
    for nome, media, dev in zip(X.columns, res.importances_mean, res.importances_std):
        etichetta, testo = SIGNIFICATO.get(nome, (nome, ""))
        out.append(VariabileImportanza(
            campo=nome,
            etichetta=etichetta,
            importanza=round(float(media), 4),
            incertezza=round(float(dev), 4),
            quota=round(max(0.0, float(media)) / totale * 100, 1),
            significato=testo,
        ))

    out.sort(key=lambda v: v.importanza, reverse=True)
    _cache = out
    return out
