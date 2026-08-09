"""Classificazione stilistica del vino a partire dai dati chimici.

Modulo condiviso da src/naming.py (nomi descrittivi) e src/pairing.py
(abbinamenti): le soglie vivono in un solo posto, cosi' un vino non puo'
essere chiamato "Abboccato" dal generatore di nomi e trattato come dolce da
quello degli abbinamenti.

DOLCEZZA - criterio normativo, non arbitrario
---------------------------------------------
Le soglie seguono il Regolamento (UE) 2019/33, Allegato III, che classifica
i vini fermi in base allo zucchero residuo prevedendo una correzione per
l'acidita': a parita' di zucchero, un vino piu' acido e' percepito piu'
secco, e la norma ne tiene conto.

    secco      <= 4 g/L, oppure <= 9 g/L se acidita' >= zucchero - 2
    abboccato  <= 12 g/L, oppure <= 18 g/L se acidita' >= zucchero - 10
    amabile    12 - 45 g/L
    dolce      > 45 g/L

Nota sul dato usato: il dataset UCI riporta `fixed_acidity` (acido tartarico
in g/dm3), mentre la norma fa riferimento all'acidita' totale. E' un proxy,
non la grandezza esatta: l'acidita' fissa ne rappresenta la componente
prevalente. La scelta e' dichiarata in docs/model_limitations.md.

CORPO - dalla gradazione alcolica
----------------------------------
L'alcol e' il proxy di struttura disponibile in questo dataset (mancano
tannini, estratto secco, glicerolo).

ACIDITA' PERCEPITA - dal pH
----------------------------
Serve a dare un secondo descrittore ai vini secchi, che nel dataset sono il
78%: siccome "secco" e' la condizione implicita di un vino da tavola e non
si menziona nel nome, al suo posto si usa la sensazione di freschezza.
"""

# --- Dolcezza (Reg. UE 2019/33, Allegato III) ---------------------------

SECCO_BASE = 4.0
SECCO_CON_ACIDITA = 9.0
ABBOCCATO_BASE = 12.0
ABBOCCATO_CON_ACIDITA = 18.0
AMABILE_MAX = 45.0


def sweetness_category(sugar: float, acidity: float) -> str:
    """Categoria di dolcezza secondo la norma UE, con correzione acidita'."""
    if sugar <= SECCO_BASE or (sugar <= SECCO_CON_ACIDITA and acidity >= sugar - 2):
        return "secco"
    if sugar <= ABBOCCATO_BASE or (
        sugar <= ABBOCCATO_CON_ACIDITA and acidity >= sugar - 10
    ):
        return "abboccato"
    if sugar <= AMABILE_MAX:
        return "amabile"
    return "dolce"


# --- Corpo (gradazione alcolica) ----------------------------------------

def body_category(alcohol: float) -> str:
    """Corpo del vino stimato dal grado alcolico.

    L'alcol non e' il corpo, ma ne e' il migliore indicatore disponibile qui:
    la struttura dipende anche da estratto secco, glicerina e tannini, che il
    dataset non contiene. Le soglie (9,5 e 12,0% vol) seguono l'uso corrente
    nella descrizione dei vini da tavola.

    E' anche la variabile piu' correlata con la qualita' percepita (+0.444,
    vedi src/eda.py), il che rende la classificazione coerente con il resto
    della piattaforma invece che una scala parallela.
    """
    if alcohol >= 12.0:
        return "corposo"
    if alcohol <= 9.5:
        return "leggero"
    return "equilibrato"


# --- Acidita' percepita (pH) --------------------------------------------

def acidity_category(ph: float) -> str:
    """pH basso = piu' acido = sensazione fresca; pH alto = morbido."""
    if ph <= 3.15:
        return "fresco"
    if ph >= 3.40:
        return "morbido"
    return "armonico"
