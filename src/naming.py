"""Genera db/migration/V4__add_wine_names.sql: nomi descrittivi per il catalogo.

Il dataset UCI di origine e' puramente analitico (misure chimiche di
laboratorio), senza nomi commerciali. Per rendere il catalogo presentabile
in una demo generiamo nomi descrittivi derivati direttamente dalle
caratteristiche chimiche del vino (non nomi di fantasia scollegati dai dati,
e non nomi che imitano marchi/cantine reali esistenti). Il criterio e'
dichiarato esplicitamente nella dichiarazione etica del progetto.

Struttura del nome: <tipo> <corpo> <secondo descrittore> [Riserva] - Lotto #id

Il secondo descrittore segue il registro enologico reale:

  - "Secco" NON compare mai nel nome. E' la condizione implicita di un vino
    da tavola (nessuno chiama un Chianti "Chianti secco") e nel dataset
    riguarda il 78% dei vini: esplicitarlo renderebbe meta' del catalogo
    omonimo senza aggiungere informazione. Al suo posto i vini secchi
    portano la sensazione di freschezza derivata dal pH.
  - Abboccato, Amabile e Dolce compaiono perche' sono l'eccezione, ed e'
    quella che va segnalata. Le soglie sono quelle del Reg. UE 2019/33
    (vedi src/wine_style.py), non valori scelti a piacere: con soglie
    arbitrarie il generatore produceva combinazioni come "Corposo Dolce",
    che non appartengono al lessico enologico.
"""
import os
import sys

import pandas as pd

# Eseguito sia come script ("python src/naming.py", come da README) sia come
# modulo importato dai test ("from src.naming import ..."): nel primo caso
# sul path finisce src/, non la radice del progetto, quindi la si aggiunge.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.wine_style import acidity_category, body_category, sweetness_category

CSV = "data/wine_quality_merged.csv"
OUT = "db/migration/V4__add_wine_names.sql"
BATCH = 500


def second_descriptor(sugar: float, acidity: float, ph: float) -> str:
    """Dolcezza se il vino non e' secco, altrimenti freschezza."""
    sweetness = sweetness_category(sugar, acidity)
    if sweetness != "secco":
        return sweetness.capitalize()
    return acidity_category(ph).capitalize()


def build_name(row: pd.Series, wine_id: int) -> str:
    base = "Rosso" if row["type"] == "red" else "Bianco"
    sugar = row["residual_sugar"] if "residual_sugar" in row else row["residual sugar"]
    acidity = row["fixed_acidity"] if "fixed_acidity" in row else row["fixed acidity"]
    ph = row["ph"] if "ph" in row else row["pH"]

    corpo = body_category(row["alcohol"]).capitalize()
    desc = second_descriptor(sugar, acidity, ph)
    riserva = " Riserva" if row["quality"] >= 7 else ""
    return f"{base} {corpo} {desc}{riserva} - Lotto #{wine_id:04d}"


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
            "scollegati dai dati, non marchi reali). Soglie di dolcezza "
            "secondo Reg. UE 2019/33. Vedi dichiarazione etica.\n"
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
