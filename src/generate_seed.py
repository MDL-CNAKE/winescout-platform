"""Genera db/migration/V2__seed_wines.sql dal CSV scaricato.

I valori vengono formattati con lo stesso numero di decimali dichiarato
nello schema (V1) per evitare warning "Data truncated": i float64 di
pandas hanno artefatti di rappresentazione binaria (es. 0.99780000000001)
che altrimenti superano la scala DECIMAL della colonna.
"""
import pandas as pd

CSV, OUT, BATCH = "data/wine_quality_merged.csv", "db/migration/V2__seed_wines.sql", 500

# Colonna -> numero di decimali, deve combaciare con V1__init_schema.sql
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


def row_sql(r):
    vals = [f"'{r['type']}'"]
    for c in SCALES:
        vals.append(f"{float(r[c]):.{SCALES[c]}f}")
    vals.append(str(int(r["quality"])))
    return "(" + ",".join(vals) + ")"


with open(OUT, "w") as f:
    f.write("-- Seed generato da src/generate_seed.py, non modificare a mano\n")
    for start in range(0, len(df), BATCH):
        chunk = df.iloc[start:start + BATCH]
        f.write("INSERT INTO wines (type,fixed_acidity,volatile_acidity,citric_acid,"
                "residual_sugar,chlorides,free_sulfur_dioxide,total_sulfur_dioxide,"
                "density,ph,sulphates,alcohol,quality) VALUES\n")
        f.write(",\n".join(row_sql(r) for _, r in chunk.iterrows()) + ";\n")

print(f"OK: {len(df)} righe scritte in {OUT}")
