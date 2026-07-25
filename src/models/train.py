"""Addestra il modello di predizione della qualita del vino.

La scelta di RandomForestRegressor non e' arbitraria: e' stata confrontata
con GradientBoosting e LinearRegression tramite 5-fold cross-validation in
compare_models.py, risultando nettamente migliore su tutte le metriche
(RMSE 0.603 vs 0.683 vs 0.734, R2 0.522 vs 0.387 vs 0.292). Questo script
riporta sia le metriche di cross-validation (stima robusta e generalizzabile)
sia quelle su un test set indipendente (valutazione finale del modello che
verra' effettivamente salvato e usato in produzione).
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
from sklearn.model_selection import KFold, cross_validate, train_test_split
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


def main() -> None:
    df = load_from_db()
    X, y = df[CAT + NUM], df["quality"]

    # --- Fase 1: cross-validation, per una stima robusta delle metriche ---
    # Un singolo train/test split puo essere ottimista o pessimista per caso;
    # la media su 5 fold e' una stima piu affidabile delle performance reali.
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    scoring = {"rmse": "neg_root_mean_squared_error", "mae": "neg_mean_absolute_error", "r2": "r2"}
    scores = cross_validate(build_pipeline(), X, y, cv=cv, scoring=scoring, n_jobs=-1)
    print(f"5-fold CV - RMSE: {-np.mean(scores['test_rmse']):.3f} (+/- {np.std(scores['test_rmse']):.3f}) | "
          f"MAE: {-np.mean(scores['test_mae']):.3f} | R2: {np.mean(scores['test_r2']):.3f}")

    # --- Fase 2: modello finale su train/test split, quello effettivamente salvato ---
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=df["type"])
    model = build_pipeline()
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    rmse = mean_squared_error(y_test, pred) ** 0.5
    print(f"Test set ({len(y_test)} vini) - RMSE: {rmse:.3f} | "
          f"MAE: {mean_absolute_error(y_test, pred):.3f} | R2: {r2_score(y_test, pred):.3f}")

    Path("models").mkdir(exist_ok=True)
    joblib.dump(model, "models/quality_model.pkl")
    print("Modello salvato in models/quality_model.pkl")


if __name__ == "__main__":
    main()
