"""Addestra il modello di qualita: Pipeline scikit-learn, valutazione, salvataggio joblib."""
from pathlib import Path
import joblib
import pandas as pd
import mysql.connector
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DB = dict(host="127.0.0.1", port=3306, user="winescout",
          password="winescout", database="winescout")
NUM = ["fixed_acidity", "volatile_acidity", "citric_acid", "residual_sugar",
       "chlorides", "free_sulfur_dioxide", "total_sulfur_dioxide",
       "density", "ph", "sulphates", "alcohol"]
CAT = ["type"]

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

def main() -> None:
    df = load_from_db()
    X, y = df[CAT + NUM], df["quality"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=df["type"])
    pre = ColumnTransformer([
        ("num", StandardScaler(), NUM),
        ("cat", OneHotEncoder(drop="first"), CAT),
    ])
    model = Pipeline([
        ("preprocess", pre),
        ("regressor", RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)),
    ])
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
