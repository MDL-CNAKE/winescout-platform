"""Genera db/migration/V2__seed_wines.sql a partire dal CSV scaricato.

Nota tecnica importante: i valori vengono formattati esplicitamente con lo
stesso numero di decimali dichiarato nello schema (V1__init_schema.sql)
invece di usare str() diretto sui float64 di pandas. Senza questo accorgimento
i valori venivano scritti con decimali "sporchi" dovuti alla rappresentazione
binaria dei float (es. 0.99780000000001 invece di 0.9978), causando warning
"Data truncated" in MySQL in fase di inserimento. Vedi issue #26 per i dettagli.
"""
import pandas as pd

CSV, OUT, BATCH = "data/wine_quality_merged.csv", "db/migration/V2__seed_wines.sql", 500

# Colonna -> numero di decimali. Deve combaciare esattamente con la scala
# DECIMAL definita in V1__init_schema.sql.
SCALES = {
    "fixed_acidity": 2,
    "volatile_acidity": 3,
    "citric_acid": 2,
    "residual_sugar": 2,
    "chlorides": 3,
    "free_sulfur_dioxide": 1,
    "total_sulfur_dioxide": 1,
    "density": 6,
    "pH": 2,
    "sulphates": 2,
    "alcohol": 2,
}

df = pd.read_csv(CSV)
cols = ["type"] + list(SCALES.keys()) + ["quality"]
df = df[cols]


def row_sql(r: pd.Series) -> str:
    """Costruisce la tupla SQL "(valore, valore, ...)" per una riga del dataset."""
    vals = [f"'{r['type']}'"]
    for c in SCALES:
        vals.append(f"{float(r[c]):.{SCALES[c]}f}")
    vals.append(str(int(r["quality"])))
    return "(" + ",".join(vals) + ")"


with open(OUT, "w") as f:
    f.write("-- Seed generato da src/generate_seed.py, non modificare a mano\n")
    # Inserimento a batch (500 righe per INSERT) invece di una riga per
    # statement: riduce drasticamente il tempo di esecuzione della migrazione.
    for start in range(0, len(df), BATCH):
        chunk = df.iloc[start:start + BATCH]
        f.write("INSERT INTO wines (type,fixed_acidity,volatile_acidity,citric_acid,"
                "residual_sugar,chlorides,free_sulfur_dioxide,total_sulfur_dioxide,"
                "density,ph,sulphates,alcohol,quality) VALUES\n")
        f.write(",\n".join(row_sql(r) for _, r in chunk.iterrows()) + ";\n")

print(f"OK: {len(df)} righe scritte in {OUT}")
