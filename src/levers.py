"""Leve di miglioramento: dove conviene intervenire su un lotto.

L'applicazione sa gia' predire la qualita' di un vino. Questo modulo risponde
alla domanda successiva, che e' quella operativa: **su quale parametro
conviene lavorare, e quanto rende farlo**.

COME FUNZIONA
-------------
Analisi controfattuale a un parametro alla volta ("one factor at a time").
Partendo dal profilo chimico reale del lotto, ogni parametro viene spostato
di un passo realistico verso l'alto e verso il basso, tenendo fermi tutti
gli altri, e si chiede al modello come cambia il punteggio previsto. La
differenza rispetto alla previsione di partenza e' il guadagno stimato di
quella correzione.

PERCHE' "STIMATO" E NON "GARANTITO"
------------------------------------
Tre limiti da tenere presenti, dichiarati anche nell'interfaccia:

1. E' la lettura del modello, non una legge fisica. Il modello ha R2 0,56 sul
   test set: coglie la tendenza, non e' un oracolo.
2. I parametri chimici sono correlati fra loro. Nella realta' di cantina non
   si abbassa l'acidita' volatile "tenendo fermo tutto il resto": ogni
   intervento ne muove altri. L'analisi a un fattore per volta ignora queste
   interazioni ed e' quindi ottimistica.
3. Il modello e' addestrato su Vinho Verde portoghesi. Le leve valgono dentro
   quel dominio.

PERCHE' I PASSI SONO QUELLI CHE SONO
-------------------------------------
Un'analisi di sensibilita' che sposta un parametro di tre deviazioni standard
produce numeri grossi e inutili: nessuno in cantina puo' dimezzare l'alcol.
I passi qui usati sono correzioni plausibili in una lavorazione reale, ed e'
questa la differenza fra un esercizio statistico e uno strumento.
"""
from dataclasses import dataclass

import pandas as pd

# Ordine delle colonne atteso dalla pipeline addestrata.
FEATURE_ORDER = [
    "type", "fixed_acidity", "volatile_acidity", "citric_acid", "residual_sugar",
    "chlorides", "free_sulfur_dioxide", "total_sulfur_dioxide", "density", "ph",
    "sulphates", "alcohol",
]


@dataclass(frozen=True)
class Leva:
    """Un parametro su cui si puo' intervenire, con il passo realistico."""
    campo: str
    etichetta: str
    passo: float          # entita' di una correzione plausibile
    unita: str
    minimo: float         # limiti oltre i quali non ha senso spingersi
    massimo: float
    intervento: str       # come si agisce in cantina, in una riga


# I passi sono correzioni che una cantina puo' realmente applicare.
LEVE: list[Leva] = [
    Leva(
        "volatile_acidity", "Acidità volatile", 0.10, "g/L", 0.08, 1.6,
        "Igiene di cantina, controllo delle fermentazioni, travasi e "
        "protezione dall'ossigeno.",
    ),
    Leva(
        "alcohol", "Grado alcolico", 0.50, "% vol", 8.0, 15.0,
        "Momento della vendemmia e gestione della maturazione zuccherina.",
    ),
    Leva(
        "sulphates", "Solfati", 0.10, "g/L", 0.22, 2.0,
        "Aggiustamento dei sali di solfato, che influiscono su stabilita' e "
        "percezione dell'amaro.",
    ),
    Leva(
        "residual_sugar", "Zucchero residuo", 1.00, "g/L", 0.6, 65.0,
        "Punto di arresto della fermentazione.",
    ),
    Leva(
        "fixed_acidity", "Acidità fissa", 0.50, "g/L", 3.8, 16.0,
        "Correzione con acido tartarico o disacidificazione.",
    ),
    Leva(
        "chlorides", "Cloruri", 0.01, "g/L", 0.009, 0.62,
        "Qualita' dell'acqua di processo e gestione della salinita'.",
    ),
    Leva(
        "free_sulfur_dioxide", "SO2 libera", 5.0, "mg/L", 1.0, 289.0,
        "Dosaggio della solforosa ai travasi e prima dell'imbottigliamento.",
    ),
    Leva(
        "ph", "pH", 0.05, "", 2.7, 4.0,
        "Correzione dell'acidita', che sposta il pH e con esso l'efficacia "
        "della solforosa.",
    ),
]


@dataclass
class EffettoLeva:
    """Effetto stimato di UN intervento su un singolo parametro.

    "Stimato" e' la parola che conta: e' il modello a dire che spostando quel
    valore la qualita' prevista salirebbe, e il modello ha imparato
    correlazioni, non rapporti di causa. In cantina un parametro non si muove
    da solo — abbassare il pH sposta anche la solforosa attiva — quindi il
    numero indica dove guardare, non quanto si otterra' davvero.

    Il calcolo e' un controfattuale a un fattore per volta: proprio per
    questo non vanno sommati piu' effetti fra loro.
    """
    campo: str
    etichetta: str
    unita: str
    valore_attuale: float
    valore_proposto: float
    variazione: float          # di quanto si sposta il parametro
    delta_qualita: float       # guadagno stimato sul punteggio
    direzione: str             # "aumentare" | "ridurre"
    intervento: str


def analizza_leve(model, wine: dict, top_n: int = 4) -> tuple[float, list[EffettoLeva]]:
    """Restituisce la previsione di partenza e le leve piu' redditizie.

    `wine` deve contenere tutte le feature di FEATURE_ORDER. Si valutano
    entrambe le direzioni per ogni parametro e si tiene la migliore, purche'
    porti un guadagno: se nessuna direzione migliora, la leva non compare.
    """
    base_row = {k: wine[k] for k in FEATURE_ORDER}
    base_pred = float(model.predict(pd.DataFrame([base_row])[FEATURE_ORDER])[0])

    effetti: list[EffettoLeva] = []

    for leva in LEVE:
        attuale = float(base_row[leva.campo])
        migliore: EffettoLeva | None = None

        for segno in (+1, -1):
            proposto = attuale + segno * leva.passo
            # Fuori dai limiti fisiologici la simulazione non ha senso.
            if proposto < leva.minimo or proposto > leva.massimo:
                continue

            row = dict(base_row)
            row[leva.campo] = proposto
            pred = float(model.predict(pd.DataFrame([row])[FEATURE_ORDER])[0])
            delta = pred - base_pred

            if delta <= 0.001:
                continue
            if migliore is not None and delta <= migliore.delta_qualita:
                continue

            migliore = EffettoLeva(
                campo=leva.campo,
                etichetta=leva.etichetta,
                unita=leva.unita,
                valore_attuale=round(attuale, 3),
                valore_proposto=round(proposto, 3),
                variazione=round(segno * leva.passo, 3),
                delta_qualita=round(delta, 3),
                direzione="aumentare" if segno > 0 else "ridurre",
                intervento=leva.intervento,
            )

        if migliore is not None:
            effetti.append(migliore)

    effetti.sort(key=lambda e: e.delta_qualita, reverse=True)
    return round(base_pred, 2), effetti[:top_n]
