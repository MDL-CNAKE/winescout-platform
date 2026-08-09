"""Confronta piu algoritmi di regressione tramite k-fold cross-validation.

Obiettivo: motivare con dati (non con intuizione) la scelta dell'algoritmo
finale usato in train.py.

PERCHE' IL CONFRONTO VIENE FATTO DUE VOLTE
------------------------------------------
Il dataset contiene 1.177 righe duplicate su 6.497 (vedi src/eda.py). Con una
cross-validation che mescola a caso, le copie finiscono su lati opposti dei
fold e ogni modello viene premiato per averle memorizzate.

Ma il premio NON e' uguale per tutti, ed e' il motivo per cui questo confronto
andava rifatto e non solo corretto. Una LinearRegression non puo' memorizzare
una singola riga: non ne ha la capacita', puo' solo tracciare un piano. Una
RandomForest con 200 alberi si', ed e' esattamente cio' che fa meglio.

Il dubbio legittimo era quindi: il vantaggio della RandomForest e' capacita'
di predire, o premio alla memorizzazione? Lo script riporta entrambe le
cross-validation - contaminata e raggruppata - cosi' il divario per ciascun
modello si legge direttamente, e la classifica si puo' confrontare.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GroupKFold, KFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.database.connection import DatabaseConnection

NUM = ["fixed_acidity", "volatile_acidity", "citric_acid", "residual_sugar",
       "chlorides", "free_sulfur_dioxide", "total_sulfur_dioxide",
       "density", "ph", "sulphates", "alcohol"]
CAT = ["type"]

# I tre algoritmi confrontati: uno lineare semplice (baseline), uno ensemble
# a bagging (RandomForest) e uno ensemble a boosting (GradientBoosting) -
# scelta che copre le famiglie di modelli viste a lezione.
MODELS = {
    "LinearRegression": LinearRegression(),
    "RandomForest": RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1),
    "GradientBoosting": GradientBoostingRegressor(random_state=42),
}


def load_from_db() -> pd.DataFrame:
    """Carica i dati di training da MySQL (stessa fonte usata da train.py)."""
    with DatabaseConnection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT type, " + ", ".join(NUM) + ", quality FROM wines")
        df = pd.DataFrame(cur.fetchall(), columns=[c[0] for c in cur.description])
        cur.close()
    df[NUM] = df[NUM].astype(float)
    df["quality"] = df["quality"].astype(int)
    return df


def build_pipeline(estimator) -> Pipeline:
    """Pipeline di preprocessing identica per tutti i modelli confrontati,
    cosi il confronto misura solo la differenza tra algoritmi e non tra
    preprocessing diversi."""
    pre = ColumnTransformer([
        ("num", StandardScaler(), NUM),
        ("cat", OneHotEncoder(drop="first"), CAT),
    ])
    return Pipeline([("preprocess", pre), ("regressor", estimator)])


def firma_chimica(df: pd.DataFrame) -> pd.Series:
    """Righe chimicamente identiche condividono la firma, quindi restano
    sempre nello stesso fold."""
    return df[NUM].astype(str).agg("|".join, axis=1)


def confronta(X, y, cv, gruppi=None) -> pd.DataFrame:
    scoring = {"rmse": "neg_root_mean_squared_error",
               "mae": "neg_mean_absolute_error", "r2": "r2"}
    righe = []
    for nome, estimatore in MODELS.items():
        scores = cross_validate(
            build_pipeline(estimatore), X, y, groups=gruppi,
            cv=cv, scoring=scoring, n_jobs=-1,
        )
        righe.append({
            "modello": nome,
            "RMSE": -np.mean(scores["test_rmse"]),
            "MAE": -np.mean(scores["test_mae"]),
            "R2": np.mean(scores["test_r2"]),
        })
    return pd.DataFrame(righe).sort_values("RMSE")


def main() -> None:
    df = load_from_db()
    X, y = df[CAT + NUM], df["quality"]
    gruppi = firma_chimica(df)
    pd.set_option("display.float_format", lambda x: f"{x:.4f}")

    contaminata = confronta(X, y, KFold(n_splits=5, shuffle=True, random_state=42))
    onesta = confronta(X, y, GroupKFold(n_splits=5), gruppi=gruppi)

    print("\n5-fold CV CONTAMINATA (KFold shuffle: le copie attraversano i fold)\n")
    print(contaminata.to_string(index=False))

    print("\n\n5-fold CV RAGGRUPPATA (GroupKFold sulla firma chimica)\n")
    print(onesta.to_string(index=False))

    # Quanto guadagna ciascun modello dalla fuga di informazione.
    print("\n\nGUADAGNO DA MEMORIZZAZIONE (R2 contaminato meno R2 raggruppato)\n")
    guadagni = (
        contaminata.set_index("modello")["R2"] - onesta.set_index("modello")["R2"]
    ).sort_values(ascending=False)
    for nome, delta in guadagni.items():
        print(f"  {nome:<20} {delta:+.4f}")
    print()
    print("Un modello ad alta capacita' puo' memorizzare una riga; una")
    print("regressione lineare no, puo' solo tracciare un piano. Se il guadagno")
    print("fosse molto diverso fra i modelli, parte del vantaggio dei piu'")
    print("complessi sarebbe premio alla memoria e non capacita' di predire.")

    print()
    print(f"Migliore per RMSE (contaminata):  {contaminata.iloc[0]['modello']}")
    print(f"Migliore per RMSE (raggruppata):  {onesta.iloc[0]['modello']}")
    if contaminata.iloc[0]["modello"] != onesta.iloc[0]["modello"]:
        print("\nLA CLASSIFICA CAMBIA: la scelta dell'algoritmo era viziata dal")
        print("leakage e va rifatta sulla base della valutazione raggruppata.")
    else:
        print("\nLa classifica NON cambia: la scelta dell'algoritmo regge anche")
        print("senza fuga, pur con metriche assolute piu' basse.")


if __name__ == "__main__":
    main()
