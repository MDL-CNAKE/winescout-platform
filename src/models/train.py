"""Addestra il modello di predizione della qualita del vino.

La scelta di RandomForestRegressor non e' arbitraria: e' stata confrontata con
GradientBoosting e LinearRegression in compare_models.py, dove resta prima su
tutte le metriche anche con cross-validation raggruppata (R2 0.385 contro
0.364 e 0.289).

Il vantaggio pero' e' modesto, e va detto: contro il GradientBoosting sono
0.021 di R2, con uno scarto tipo di 0.015 sull'RMSE fra i fold. La formula
"nettamente migliore" che compariva qui era basata sul confronto contaminato,
dove il divario appariva sei volte piu' grande - perche' la fuga premia i
modelli capaci di memorizzare, e una foresta di 200 alberi lo e' molto piu' di
una retta.

VALUTAZIONE RAGGRUPPATA. Il dataset contiene 1.177 righe perfettamente
duplicate su 6.497 (18%). Uno split casuale ne manda una in addestramento e la
copia in test, e il modello viene premiato per averla memorizzata: le prime
versioni di questo script riportavano R2 0.522 in CV e 0.561 su test, valori
gonfiati di circa il 29%. Ora sia la cross-validation sia lo split finale
raggruppano per firma chimica, cosi' le copie non attraversano mai la
divisione. Le metriche che escono sono piu' basse e sono quelle vere.

L'analisi che ha portato alla scoperta e' in src/eda.py, la misura del
gonfiaggio in src/models/leakage_experiment.py.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.database.connection import DatabaseConnection

# Feature numeriche (chimiche) e categoriche (tipo di vino) usate dal modello.
NUM = ["fixed_acidity", "volatile_acidity", "citric_acid", "residual_sugar",
       "chlorides", "free_sulfur_dioxide", "total_sulfur_dioxide",
       "density", "ph", "sulphates", "alcohol"]
CAT = ["type"]


def load_from_db() -> pd.DataFrame:
    """Carica i dati di training direttamente da MySQL (non dal CSV).

    Il database e', per requisito di progetto, lo storage primario: leggere
    da MySQL invece che dal CSV garantisce che il modello sia sempre
    allineato con i dati effettivamente persistiti (es. se in futuro si
    aggiungono vini dal catalogo tramite l'app, il modello li vedrebbe).
    """
    with DatabaseConnection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT type, " + ", ".join(NUM) + ", quality FROM wines")
        df = pd.DataFrame(cur.fetchall(), columns=[c[0] for c in cur.description])
        cur.close()
    df[NUM] = df[NUM].astype(float)
    df["quality"] = df["quality"].astype(int)
    return df


def build_pipeline() -> Pipeline:
    """Costruisce la Pipeline scikit-learn: preprocessing + modello.

    Incapsulare preprocessing e modello in un'unica Pipeline (invece di
    trasformare i dati a mano prima del fit) garantisce che le stesse
    trasformazioni vengano applicate in modo identico sia in training sia in
    inferenza (predict), evitando data leakage e bug di disallineamento.
    """
    pre = ColumnTransformer([
        ("num", StandardScaler(), NUM),          # standardizza le feature chimiche
        ("cat", OneHotEncoder(drop="first"), CAT),  # codifica red/white
    ])
    return Pipeline([
        ("preprocess", pre),
        ("regressor", RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)),
    ])


def firma_chimica(df: pd.DataFrame) -> pd.Series:
    """Identificativo di gruppo per righe chimicamente identiche.

    Il dataset contiene 1.177 righe perfettamente duplicate su 6.497 (18%).
    Con uno split casuale una riga finisce in addestramento e la sua copia in
    test: il modello viene valutato su dati che ha gia' memorizzato, e la
    memorizzazione e' cio' che una Random Forest fa meglio.

    Raggruppando per firma chimica, le copie restano sempre dalla stessa parte
    dello split. Misurato in src/models/leakage_experiment.py: senza questo
    accorgimento l'R2 passava da 0.398 a 0.561, cioe' il 29% del punteggio
    veniva da righe gia' viste.

    Si raggruppa invece di deduplicare per non buttare il 18% dei dati: le
    copie restano utili in addestramento, devono solo smettere di comparire
    in valutazione.
    """
    return df[NUM].astype(str).agg("|".join, axis=1)


def main() -> None:
    """Addestra, valuta senza fuga e salva il modello in models/quality_model.pkl."""
    df = load_from_db()
    X, y = df[CAT + NUM], df["quality"]
    gruppi = firma_chimica(df)

    # --- Fase 1: cross-validation raggruppata ---
    # ATTENZIONE: KFold(shuffle=True) NON protegge da questo problema, perche'
    # sparge le copie fra i fold esattamente come farebbe uno split casuale.
    # La cross-validation e' una difesa contro la sfortuna del singolo split,
    # non contro la contaminazione dei dati. Serve GroupKFold.
    cv = GroupKFold(n_splits=5)
    scoring = {"rmse": "neg_root_mean_squared_error", "mae": "neg_mean_absolute_error", "r2": "r2"}
    scores = cross_validate(
        build_pipeline(), X, y, groups=gruppi, cv=cv, scoring=scoring, n_jobs=-1
    )
    print(f"5-fold CV raggruppata - RMSE: {-np.mean(scores['test_rmse']):.3f} "
          f"(+/- {np.std(scores['test_rmse']):.3f}) | "
          f"MAE: {-np.mean(scores['test_mae']):.3f} | R2: {np.mean(scores['test_r2']):.3f}")

    # --- Fase 2: modello finale, valutato su un test set senza copie ---
    # Si perde la stratificazione per tipo che train_test_split consentiva:
    # con 6.497 righe e una ripartizione rosso/bianco molto sbilanciata il
    # campionamento casuale dei gruppi la rispetta comunque a sufficienza, e
    # l'assenza di fuga vale piu' della stratificazione perfetta.
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    idx_train, idx_test = next(splitter.split(X, y, groups=gruppi))
    X_train, X_test = X.iloc[idx_train], X.iloc[idx_test]
    y_train, y_test = y.iloc[idx_train], y.iloc[idx_test]

    model = build_pipeline()
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    rmse = mean_squared_error(y_test, pred) ** 0.5
    print(f"Test set ({len(y_test)} vini, nessuna copia condivisa col train) - "
          f"RMSE: {rmse:.3f} | MAE: {mean_absolute_error(y_test, pred):.3f} | "
          f"R2: {r2_score(y_test, pred):.3f}")

    Path("models").mkdir(exist_ok=True)
    joblib.dump(model, "models/quality_model.pkl")
    print("Modello salvato in models/quality_model.pkl")


if __name__ == "__main__":
    main()
