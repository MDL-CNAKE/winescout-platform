"""Addestra il modello di qualita: Pipeline scikit-learn, valutazione, salvataggio joblib.

La scelta di RandomForestRegressor e' motivata dal confronto in
compare_models.py (5-fold CV): RMSE 0.603 vs 0.683 (GradientBoosting)
vs 0.734 (LinearRegression), R2 0.522 vs 0.387 vs 0.292.
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

NUM = ["fixed_acidity", "volatile_acidity", "citric_acid", "residual_sugar",
       "chlorides", "free_sulfur_dioxide", "total_sulfur_dioxide",
       "density", "ph", "sulphates", "alcohol"]
CAT = ["type"]


def load_from_db() -> pd.DataFrame:
    with DatabaseConnection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT type, " + ", ".join(NUM) + ", quality FROM wines")
        df = pd.DataFrame(cur.fetchall(), columns=[c[0] for c in cur.description])
        cur.close()
    df[NUM] = df[NUM].astype(float)
    df["quality"] = df["quality"].astype(int)
    return df


def build_pipeline() -> Pipeline:
    pre = ColumnTransformer([
        ("num", StandardScaler(), NUM),
        ("cat", OneHotEncoder(drop="first"), CAT),
    ])
    return Pipeline([
        ("preprocess", pre),
        ("regressor", RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)),
    ])


def main() -> None:
    df = load_from_db()
    X, y = df[CAT + NUM], df["quality"]

    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    scoring = {"rmse": "neg_root_mean_squared_error", "mae": "neg_mean_absolute_error", "r2": "r2"}
    scores = cross_validate(build_pipeline(), X, y, cv=cv, scoring=scoring, n_jobs=-1)
    print(f"5-fold CV - RMSE: {-np.mean(scores['test_rmse']):.3f} (+/- {np.std(scores['test_rmse']):.3f}) | "
          f"MAE: {-np.mean(scores['test_mae']):.3f} | R2: {np.mean(scores['test_r2']):.3f}")

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
