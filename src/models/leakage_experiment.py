"""Quanto sono gonfiate le metriche del modello a causa dei duplicati?

IL PROBLEMA
-----------
Il dataset contiene 1.177 righe perfettamente identiche su 6.497 (18%).
`train_test_split` divide a caso: una riga finisce in addestramento e la sua
copia identica in test. Il modello viene interrogato su dati che ha gia'
memorizzato, e la memorizzazione e' esattamente cio' che una Random Forest fa
meglio. Il punteggio che ne esce non misura la capacita' di generalizzare ma,
in parte, la capacita' di ricordare.

E' data leakage. Non riguarda il preprocessing - la Pipeline lo evita gia'
correttamente - ma la composizione stessa dei dati, che nessuna Pipeline puo'
sistemare.

TRE SCENARI, E PERCHE' SERVONO TUTTI E TRE
------------------------------------------
A. ATTUALE - split casuale su tutti i dati. E' cio' che fa train.py oggi.

B. DEDUPLICATO - si tolgono le copie, poi si divide. Sembra la correzione
   ovvia, ma cambia DUE cose insieme: elimina la fuga di informazione e
   riduce il dataset del 18%. Un calo dell'R2 fra A e B non direbbe quale
   delle due cause lo ha prodotto.

C. RAGGRUPPATO - si tengono tutte le righe, ma le copie identiche restano
   dalla stessa parte dello split (GroupShuffleSplit sulla firma chimica).
   Stessa quantita' di dati dello scenario A, zero fuga. E' il confronto che
   ISOLA il leakage, ed e' il motivo per cui B da solo non basterebbe.

Il confronto onesto e' A contro C. B serve a mostrare quanto pesa la sola
riduzione del dataset.

NOTA SULLA CROSS-VALIDATION
---------------------------
Anche la 5-fold CV di train.py e' contaminata: KFold(shuffle=True) sparge le
copie fra i fold esattamente come lo split. La versione onesta e' GroupKFold
sulla firma chimica, riportata qui sotto.

Uso: python src/models/leakage_experiment.py
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import (
    GroupKFold,
    GroupShuffleSplit,
    KFold,
    cross_val_score,
    train_test_split,
)

from src.models.train import CAT, NUM, build_pipeline

CSV = "data/wine_quality_merged.csv"

# Nel CSV la colonna e' "pH"; nel database e nel modello e' "ph". Si allinea
# al nome usato dalla Pipeline, altrimenti il ColumnTransformer non trova la
# colonna e fallisce in modo poco leggibile.
RINOMINA = {"pH": "ph"}


def carica() -> pd.DataFrame:
    """Legge dal CSV e non dal database.

    train.py legge da MySQL perche' in produzione il database e' la fonte
    primaria. Qui si legge il CSV: e' lo stesso identico contenuto (il seed
    del database viene generato da questo file), ma rende l'esperimento
    eseguibile senza container attivo - cioe' riproducibile da chiunque
    scarichi il progetto.
    """
    df = pd.read_csv(CSV).rename(columns=RINOMINA)
    return df


def firma_chimica(df: pd.DataFrame) -> pd.Series:
    """Identificativo di gruppo: righe con la stessa chimica hanno la stessa
    firma, e quindi non potranno finire su lati opposti dello split."""
    return df[NUM].astype(str).agg("|".join, axis=1)


def valuta(X_train, X_test, y_train, y_test) -> dict:
    model = build_pipeline()
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    return {
        "n_train": len(y_train),
        "n_test": len(y_test),
        "rmse": mean_squared_error(y_test, pred) ** 0.5,
        "mae": mean_absolute_error(y_test, pred),
        "r2": r2_score(y_test, pred),
    }


def scenario_attuale(df: pd.DataFrame) -> dict:
    X, y = df[CAT + NUM], df["quality"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=df["type"]
    )
    return valuta(X_train, X_test, y_train, y_test)


def scenario_deduplicato(df: pd.DataFrame) -> dict:
    pulito = df.drop_duplicates()
    X, y = pulito[CAT + NUM], pulito["quality"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=pulito["type"]
    )
    return valuta(X_train, X_test, y_train, y_test)


def scenario_raggruppato(df: pd.DataFrame) -> dict:
    """Tutte le righe, ma le copie identiche restano dalla stessa parte."""
    X, y = df[CAT + NUM], df["quality"]
    gruppi = firma_chimica(df)
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    idx_train, idx_test = next(splitter.split(X, y, groups=gruppi))
    return valuta(
        X.iloc[idx_train], X.iloc[idx_test], y.iloc[idx_train], y.iloc[idx_test]
    )


def cross_validation(df: pd.DataFrame) -> tuple[float, float]:
    """CV contaminata (KFold) contro CV onesta (GroupKFold)."""
    X, y = df[CAT + NUM], df["quality"]
    gruppi = firma_chimica(df)

    contaminata = cross_val_score(
        build_pipeline(), X, y, cv=KFold(n_splits=5, shuffle=True, random_state=42),
        scoring="r2", n_jobs=-1,
    )
    onesta = cross_val_score(
        build_pipeline(), X, y, cv=GroupKFold(n_splits=5), groups=gruppi,
        scoring="r2", n_jobs=-1,
    )
    return float(np.mean(contaminata)), float(np.mean(onesta))


def main() -> None:
    df = carica()
    print(f"Dataset: {len(df)} righe, {len(df.drop_duplicates())} uniche "
          f"({df.duplicated().sum()} duplicati)\n")

    a = scenario_attuale(df)
    c = scenario_raggruppato(df)
    b = scenario_deduplicato(df)

    print(f"{'scenario':<28} {'train':>7} {'test':>7} {'RMSE':>7} {'MAE':>7} {'R2':>7}")
    print("-" * 68)
    for nome, s in (
        ("A. attuale (split casuale)", a),
        ("C. raggruppato (no fuga)", c),
        ("B. deduplicato", b),
    ):
        print(f"{nome:<28} {s['n_train']:>7} {s['n_test']:>7} "
              f"{s['rmse']:>7.3f} {s['mae']:>7.3f} {s['r2']:>7.3f}")

    delta = a["r2"] - c["r2"]
    print()
    print("=" * 68)
    print(f"Gonfiaggio isolato (A meno C): R2 {delta:+.3f}")
    if a["r2"] > 0:
        print(f"cioe' il {100 * delta / a['r2']:.0f}% del punteggio dichiarato viene")
        print("dall'aver rivisto in test righe gia' presenti in addestramento.")
    print("=" * 68)

    contaminata, onesta = cross_validation(df)
    print()
    print(f"5-fold CV contaminata (KFold shuffle):  R2 {contaminata:.3f}")
    print(f"5-fold CV onesta      (GroupKFold):     R2 {onesta:.3f}")
    print()
    print("La cross-validation non protegge da questo problema: mescolare i")
    print("fold sparge le copie esattamente come lo split. Serve raggruppare.")


if __name__ == "__main__":
    main()
