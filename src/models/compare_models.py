"""Confronta piu algoritmi di regressione con k-fold cross-validation.
Uso: python src/models/compare_models.py
Produce una tabella RMSE/MAE/R2 per motivare la scelta del modello finale.
"""
import numpy as np
import pandas as pd
import mysql.connector
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DB = dict(host="127.0.0.1", port=3306, user="winescout",
          password="winescout", database="winescout")
NUM = ["fixed_acidity", "volatile_acidity", "citric_acid", "residual_sugar",
       "chlorides", "free_sulfur_dioxide", "total_sulfur_dioxide",
       "density", "ph", "sulphates", "alcohol"]
CAT = ["type"]

MODELS = {
    "LinearRegression": LinearRegression(),
    "RandomForest": RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1),
    "GradientBoosting": GradientBoostingRegressor(random_state=42),
}


def load_from_db() -> pd.DataFrame:
    try:
        conn = mysql.connector.connect(**DB)
    except mysql.connector.Error as e:
        raise RuntimeError(f"Connessione MySQL fallita (docker compose up -d mysql?): {e}") from e
    cur = conn.cursor()
    cur.execute("SELECT type, " + ", ".join(NUM) + ", quality FROM wines")
    df = pd.DataFrame(cur.fetchall(), columns=[c[0] for c in cur.description])
    conn.close()
    df[NUM] = df[NUM].astype(float)
    df["quality"] = df["quality"].astype(int)
    return df


def build_pipeline(estimator) -> Pipeline:
    pre = ColumnTransformer([
        ("num", StandardScaler(), NUM),
        ("cat", OneHotEncoder(drop="first"), CAT),
    ])
    return Pipeline([("preprocess", pre), ("regressor", estimator)])


def main() -> None:
    df = load_from_db()
    X, y = df[CAT + NUM], df["quality"]
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    scoring = {"rmse": "neg_root_mean_squared_error", "mae": "neg_mean_absolute_error", "r2": "r2"}

    rows = []
    for name, estimator in MODELS.items():
        pipe = build_pipeline(estimator)
        scores = cross_validate(pipe, X, y, cv=cv, scoring=scoring, n_jobs=-1)
        rows.append({
            "modello": name,
            "RMSE_media": -np.mean(scores["test_rmse"]),
            "RMSE_std": np.std(scores["test_rmse"]),
            "MAE_media": -np.mean(scores["test_mae"]),
            "R2_media": np.mean(scores["test_r2"]),
        })

    result = pd.DataFrame(rows).sort_values("RMSE_media")
    pd.set_option("display.float_format", lambda x: f"{x:.4f}")
    print("\nConfronto modelli - 5-fold cross-validation\n")
    print(result.to_string(index=False))
    print(f"\nMigliore per RMSE: {result.iloc[0]['modello']}")


if __name__ == "__main__":
    main()
