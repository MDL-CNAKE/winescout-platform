"""Genera db/migration/V3__add_pricing.sql: prezzo e margine simulati.

Il dataset UCI di partenza non contiene informazioni commerciali (e' un
dataset di analisi chimica per la ricerca enologica), quindi prezzo e margine
sono simulati con una logica di business esplicita e motivata, non generati
a caso. Questo e' dichiarato esplicitamente nella dichiarazione etica del
progetto (limiti del sistema: dati commerciali non reali).

Logica di business:
- Prezzo: dipende dal tipo di vino (i rossi hanno in media un prezzo di
  listino piu alto dei bianchi in una cantina artigianale italiana) e dal
  punteggio qualita (i vini piu premiati costano di piu), con una variazione
  casuale controllata per evitare una relazione troppo meccanica.
- Margine %: inversamente proporzionale al prezzo. Riflette una prassi reale
  della ristorazione e della distribuzione enologica: sui vini da tavola ad
  alto turnover si applica un margine percentuale piu alto (bassa spesa,
  alta rotazione), mentre sui vini pregiati il margine percentuale e' piu
  contenuto pur restando piu alto in valore assoluto (minore rotazione,
  posizionamento premium).
"""
import numpy as np
import pandas as pd

CSV = "data/wine_quality_merged.csv"
OUT = "db/migration/V3__add_pricing.sql"
BATCH = 500

# Fascia di prezzo al pubblico (EUR) per tipo di vino, ai due estremi di qualita.
PRICE_RANGE = {"red": (8.0, 35.0), "white": (6.0, 28.0)}

# Seed fisso per riproducibilita: rieseguendo lo script si ottengono sempre
# gli stessi prezzi, utile per non invalidare test o demo gia preparate.
RNG = np.random.RandomState(42)


def compute_price(row: pd.Series) -> float:
    """Calcola il prezzo simulato di un vino in base a tipo e qualita."""
    lo, hi = PRICE_RANGE[row["type"]]
    q_norm = (row["quality"] - 3) / (9 - 3)  # normalizza qualita 3-9 in 0-1
    noise = RNG.normal(0, 1.5)  # variazione realistica, non tutti i vini alla stessa qualita costano identico
    price = lo + q_norm * (hi - lo) + noise
    return round(float(np.clip(price, lo * 0.8, hi * 1.15)), 2)


def compute_margin(price: float, type_: str) -> float:
    """Calcola il margine percentuale simulato, inversamente legato al prezzo."""
    lo, hi = PRICE_RANGE[type_]
    price_ratio = (price - lo) / (hi - lo) if hi > lo else 0
    price_ratio = float(np.clip(price_ratio, 0, 1))
    noise = RNG.normal(0, 3)
    # ~68% di margine su un vino entry level, ~35% su un vino premium
    margin = 68 - price_ratio * 33 + noise
    return round(float(np.clip(margin, 25, 70)), 2)


def main() -> None:
    df = pd.read_csv(CSV).reset_index(drop=True)
    # L'id qui deve combaciare con l'ordine di inserimento usato da
    # generate_seed.py (stesso CSV, stesso ordine di lettura), altrimenti
    # prezzo e margine finirebbero sul vino sbagliato.
    df["id"] = df.index + 1

    rows = []
    for _, r in df.iterrows():
        price = compute_price(r)
        margin = compute_margin(price, r["type"])
        rows.append((int(r["id"]), price, margin))

    with open(OUT, "w") as f:
        f.write("-- Prezzo e margine simulati (logica in src/pricing.py), non dati reali.\n")
        f.write("ALTER TABLE wines\n")
        f.write("    ADD COLUMN price_eur DECIMAL(6,2) NULL,\n")
        f.write("    ADD COLUMN margin_pct DECIMAL(5,2) NULL;\n\n")

        # UPDATE a blocchi con CASE/WHEN invece di una UPDATE per riga:
        # stessa logica di batching gia vista in generate_seed.py, per
        # velocizzare l'esecuzione della migrazione.
        for start in range(0, len(rows), BATCH):
            chunk = rows[start:start + BATCH]
            cases_price = " ".join(f"WHEN {i} THEN {p}" for i, p, m in chunk)
            cases_margin = " ".join(f"WHEN {i} THEN {m}" for i, p, m in chunk)
            ids = ",".join(str(i) for i, p, m in chunk)
            f.write(
                f"UPDATE wines SET "
                f"price_eur = CASE id {cases_price} END, "
                f"margin_pct = CASE id {cases_margin} END "
                f"WHERE id IN ({ids});\n"
            )

    print(f"OK: migrazione scritta in {OUT} ({len(rows)} vini)")


if __name__ == "__main__":
    main()
