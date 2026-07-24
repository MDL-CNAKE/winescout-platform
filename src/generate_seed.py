"""Genera db/migration/V2__seed_wines.sql dal CSV scaricato."""
import pandas as pd

CSV, OUT, BATCH = "data/wine_quality_merged.csv", "db/migration/V2__seed_wines.sql", 500

df = pd.read_csv(CSV)
cols = ["type","fixed_acidity","volatile_acidity","citric_acid","residual_sugar",
        "chlorides","free_sulfur_dioxide","total_sulfur_dioxide","density",
        "pH","sulphates","alcohol","quality"]
df = df[cols]

def row_sql(r):
    return "(" + ",".join([f"'{r['type']}'"] + [str(r[c]) for c in cols[1:]]) + ")"

with open(OUT, "w") as f:
    f.write("-- Seed generato da src/generate_seed.py, non modificare a mano\n")
    for start in range(0, len(df), BATCH):
        chunk = df.iloc[start:start+BATCH]
        f.write("INSERT INTO wines (type,fixed_acidity,volatile_acidity,citric_acid,"
                "residual_sugar,chlorides,free_sulfur_dioxide,total_sulfur_dioxide,"
                "density,ph,sulphates,alcohol,quality) VALUES\n")
        f.write(",\n".join(row_sql(r) for _, r in chunk.iterrows()) + ";\n")

print(f"OK: {len(df)} righe scritte in {OUT}")
