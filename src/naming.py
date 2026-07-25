"""Genera db/migration/V4__add_wine_names.sql: nomi descrittivi per il catalogo.

Il dataset UCI di origine e' puramente analitico (misure chimiche di
laboratorio), senza nomi commerciali. Per rendere il catalogo presentabile
in una demo generiamo nomi descrittivi derivati direttamente dalle
caratteristiche chimiche del vino (non nomi di fantasia scollegati dai dati,
e non nomi che imitano marchi/cantine reali esistenti). Il criterio e'
dichiarato esplicitamente nella dichiarazione etica del progetto.
"""
import pandas as pd

CSV = "data/wine_quality_merged.csv"
OUT = "db/migration/V4__add_wine_names.sql"
BATCH = 500


def alcohol_descriptor(alcohol: float) -> str:
    """Descrittore principale in base al grado alcolico."""
    if alcohol >= 12.0:
        return "Corposo"
    if alcohol <= 9.5:
        return "Leggero"
    return "Equilibrato"


def sugar_descriptor(sugar: float) -> str:
    """Descrittore secondario in base allo zucchero residuo."""
    if sugar >= 10.0:
        return "Dolce"
    if sugar <= 2.0:
        return "Secco"
    return "Amabile"


def build_name(row: pd.Series, wine_id: int) -> str:
    base = "Rosso" if row["type"] == "red" else "Bianco"
    desc1 = alcohol_descriptor(row["alcohol"])
    desc2 = sugar_descriptor(row["residual sugar"] if "residual sugar" in row else row["residual_sugar"])
    riserva = " Riserva" if row["quality"] >= 7 else ""
    return f"{base} {desc1} {desc2}{riserva} - Lotto #{wine_id:04d}"


def main() -> None:
    df = pd.read_csv(CSV).reset_index(drop=True)
    df.columns = [c.replace(" ", "_") for c in df.columns]
    df["id"] = df.index + 1  # stesso ordine di generate_seed.py / pricing.py

    rows = []
    for _, r in df.iterrows():
        name = build_name(r, int(r["id"]))
        rows.append((int(r["id"]), name))

    with open(OUT, "w") as f:
        f.write(
            "-- Nomi descrittivi generati da src/naming.py in base alle "
            "caratteristiche chimiche reali del vino (non nomi di fantasia "
            "scollegati dai dati, non marchi reali). Vedi dichiarazione etica.\n"
        )
        f.write("ALTER TABLE wines ADD COLUMN name VARCHAR(80) NULL;\n\n")

        for start in range(0, len(rows), BATCH):
            chunk = rows[start:start + BATCH]
            cases = " ".join(f"WHEN {i} THEN '{n}'" for i, n in chunk)
            ids = ",".join(str(i) for i, n in chunk)
            f.write(f"UPDATE wines SET name = CASE id {cases} END WHERE id IN ({ids});\n")

    print(f"OK: migrazione scritta in {OUT} ({len(rows)} vini)")


if __name__ == "__main__":
    main()
