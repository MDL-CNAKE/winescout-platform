"""Esperimento di feature engineering: le variabili derivate migliorano il modello?

RISULTATO: no. E' un esito negativo, documentato perche' spiega qualcosa sul
dominio e non solo sul modello.

L'IPOTESI
----------
Il progetto calcola gia' diverse grandezze derivate per le regole enologiche —
in particolare l'SO2 MOLECOLARE, cioe' la frazione di solforosa realmente
attiva: SO2_libera / (1 + 10^(pH - 1,81)). Prese singolarmente, SO2 libera e pH
pesano poco nella previsione (10,5% e 3,6% di importanza per permutazione);
combinate secondo la chimica reale producono la grandezza che un enologo
guarda davvero. Sembrava ragionevole che, fornita gia' calcolata, migliorasse
la stima della qualita'.

IL RISULTATO MISURATO
----------------------
    configurazione                     CV R2     Test R2
    colonne grezze                     0,5000    0,5572
    + tutte e sei le derivate          0,5040    0,5556
    + solo SO2 molecolare              0,4985    0,5559
    + SO2 molecolare e quota libera    0,5001    0,5517

Le differenze sono nell'ordine dei millesimi e cambiano segno fra
cross-validation e test set. La dispersione fra i fold (0,005-0,008) e' piu'
ampia dello scarto fra le medie: e' rumore, non miglioramento.

Lo stesso vale per la regressione lineare (0,2924 -> 0,2958), che era il
controllo previsto: un modello lineare non puo' rappresentare rapporti ed
esponenziali, quindi avrebbe dovuto beneficiarne piu' di un albero. Non e'
successo, il che esclude la spiegazione "il RandomForest ci arriva da solo".

PERCHE'
--------
La causa non e' la ridondanza. Il denominatore 1 + 10^(pH - 1,81) varia da 9,1
a 159,5 lungo il catalogo, quindi l'SO2 molecolare non e' un riscalamento
dell'SO2 libera: correlano 0,854, non 1.

La causa e' che quella variabile **non ha relazione con il target**:

    correlazione con quality
      alcol                  +0,444
      acidita' volatile      -0,266
      SO2 libera             +0,055
      SO2 molecolare         +0,023

L'SO2 molecolare governa la TENUTA NEL TEMPO — ossidazione, rifermentazione —
mentre `quality` e' un punteggio SENSORIALE, cioe' quanto il vino piace
all'assaggio adesso. Sono fenomeni diversi: un vino puo' essere ben protetto e
mediocre, o fragile ed eccellente. Lo conferma dall'altro lato la scorrelazione
gia' misurata (0,163) fra indice di conservazione e punteggio di qualita'.

La variabile e' quindi giusta, ma per un altro obiettivo — ed e' esattamente
dove viene usata: in `src/conservation.py`.

Fa eccezione `acidita_totale_stim`, che e' un doppione vero: correla 0,994 con
l'acidita' fissa.

LA LEZIONE
-----------
L'ingegnerizzazione delle variabili non si valuta sulla bonta' della formula ma
sulla pertinenza al fenomeno che il target misura. Una grandezza corretta,
motivata e chimicamente fondata puo' non spostare nulla, se descrive qualcosa
che il target non registra.

Esecuzione:  python src/models/feature_experiment.py
"""
import os
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import mean_squared_error, r2_score

CSV = "data/wine_quality_merged.csv"

NUM = [
    "fixed_acidity", "volatile_acidity", "citric_acid", "residual_sugar",
    "chlorides", "free_sulfur_dioxide", "total_sulfur_dioxide",
    "density", "ph", "sulphates", "alcohol",
]

DERIVATE = [
    "so2_molecolare",           # frazione di solforosa attiva (SO2 libera + pH)
    "so2_quota_libera",         # quanta solforosa e' ancora disponibile
    "so2_legata",               # totale meno libera
    "rapporto_alcol_zucchero",  # equilibrio fra struttura e morbidezza
    "acidita_totale_stim",      # somma delle componenti acide
    "densita_netta",            # densita' corretta per lo zucchero
]


def carica() -> pd.DataFrame:
    df = pd.read_csv(CSV)
    df.columns = [c.replace(" ", "_") for c in df.columns]
    df = df.rename(columns={"pH": "ph"})

    df["so2_molecolare"] = df.free_sulfur_dioxide / (1 + 10 ** (df.ph - 1.81))
    df["so2_quota_libera"] = (
        df.free_sulfur_dioxide / df.total_sulfur_dioxide.replace(0, np.nan)
    ).fillna(0)
    df["so2_legata"] = df.total_sulfur_dioxide - df.free_sulfur_dioxide
    df["rapporto_alcol_zucchero"] = df.alcohol / (df.residual_sugar + 1)
    df["acidita_totale_stim"] = df.fixed_acidity + df.volatile_acidity + df.citric_acid
    df["densita_netta"] = df.density - df.residual_sugar * 0.0004
    return df


def pipeline(colonne: list[str], regressore):
    return Pipeline([
        ("pre", ColumnTransformer([
            ("num", StandardScaler(), colonne),
            ("cat", OneHotEncoder(drop="first"), ["type"]),
        ])),
        ("reg", regressore),
    ])


def valuta(df: pd.DataFrame, nome: str, colonne: list[str], regressore, folds: int = 3):
    X, y = df[["type"] + colonne], df["quality"]
    cv = KFold(n_splits=folds, shuffle=True, random_state=42)
    s = cross_validate(pipeline(colonne, regressore), X, y, cv=cv, scoring="r2", n_jobs=-1)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=df["type"]
    )
    m = pipeline(colonne, regressore)
    m.fit(X_tr, y_tr)
    pred = m.predict(X_te)

    print(
        f"{nome:34s} CV R2 {s['test_score'].mean():.4f} "
        f"(dev.std {s['test_score'].std():.4f})  |  "
        f"Test R2 {r2_score(y_te, pred):.4f}  RMSE {mean_squared_error(y_te, pred) ** 0.5:.4f}"
    )


def main() -> None:
    df = carica()

    def rf():
        return RandomForestRegressor(n_estimators=120, random_state=42, n_jobs=-1)

    print("=== RandomForest ===")
    valuta(df, "colonne grezze", NUM, rf())
    valuta(df, "+ tutte le derivate", NUM + DERIVATE, rf())
    valuta(df, "+ solo SO2 molecolare", NUM + ["so2_molecolare"], rf())

    print()
    print("=== Regressione lineare (controllo) ===")
    valuta(df, "colonne grezze", NUM, LinearRegression(), folds=5)
    valuta(df, "+ tutte le derivate", NUM + DERIVATE, LinearRegression(), folds=5)

    print()
    print("=== Perche': correlazione con il target ===")
    for c in ["alcohol", "volatile_acidity", "free_sulfur_dioxide",
              "so2_molecolare", "acidita_totale_stim"]:
        print(f"  {c:26s} r = {df[c].corr(df.quality):+.3f}")

    print()
    print("=== Ridondanza rispetto alla variabile madre ===")
    print(f"  SO2 molecolare vs SO2 libera  r = {df.so2_molecolare.corr(df.free_sulfur_dioxide):.3f}")
    print(f"  acidita stimata vs fissa      r = {df.acidita_totale_stim.corr(df.fixed_acidity):.3f}")


if __name__ == "__main__":
    main()
