"""Genera db/migration/V5__add_food_pairing.sql: abbinamento cibo-vino.

Il dataset UCI non contiene informazioni sugli abbinamenti (solo dati
chimici), quindi l'abbinamento e' derivato con un sistema a REGOLE basato
sui principi enologici standard di abbinamento per contrapposizione e
concordanza:
  - acidita e effervescenza CONTRASTANO grassezza e untuosita (sgrassano);
  - tannino e struttura CONTRASTANO succulenza e tendenza dolce delle carni;
  - la dolcezza vera (passiti, muffati) si abbina per CONCORDANZA ai dolci;
  - i vini abboccati/amabili (morbidi ma non dolci) contrastano bene la
    piccantezza e le cucine speziate/agrodolci;
  - vini leggeri con piatti semplici, vini strutturati con piatti saporiti.

Distinzione enologica chiave: un vino AMABILE non e' un vino DOLCE da
dessert. Sono due categorie di abbinamento diverse e vengono trattate
separatamente. Le soglie non sono scelte a piacere ma seguono il Reg. UE
2019/33 tramite src/wine_style.py, lo stesso modulo usato da src/naming.py:
cosi' un vino chiamato "Abboccato" nel catalogo non viene abbinato come se
fosse un passito.

Ogni regola include esempi concreti di piatti reali (cucina italiana e non)
per rendere il suggerimento immediatamente utile a un ristoratore. Le regole
sono una formalizzazione originale di principi enologici di dominio pubblico,
non riproducono testo protetto da copyright di terzi.
"""
import os
import sys

import pandas as pd

# Vedi nota in src/naming.py: lo script gira sia direttamente sia importato.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.wine_style import sweetness_category

CSV = "data/wine_quality_merged.csv"
OUT = "db/migration/V5__add_food_pairing.sql"
BATCH = 500


def pairing_for(row: pd.Series) -> str:
    """Restituisce un suggerimento di abbinamento con esempi di piatti reali."""
    alcohol = row["alcohol"]
    sugar = row["residual_sugar"] if "residual_sugar" in row else row["residual sugar"]
    acidity = row["fixed_acidity"] if "fixed_acidity" in row else row["fixed acidity"]
    is_red = row["type"] == "red"

    sweetness = sweetness_category(sugar, acidity)

    # 1. Vino DOLCE vero (oltre 45 g/L: passiti, muffati, vendemmie tardive)
    #    -> concordanza con i dolci o contrasto con erborinati importanti.
    if sweetness == "dolce":
        return "Dolci da dessert (tiramisu, cantucci, panettone) e formaggi erborinati (gorgonzola, roquefort)"

    # 2. Vino AMABILE (12-45 g/L): morbido ma non da dessert. La morbidezza
    #    contrasta piccantezza e note agrodolci.
    if sweetness == "amabile":
        return "Cucina speziata e agrodolce (curry, cucina thai, anatra all'arancia), formaggi di media stagionatura"

    # 3. Rossi corposi e alcolici -> piatti strutturati e grassi.
    if is_red and alcohol >= 12:
        return "Brasato al Barolo, cinghiale in umido, bistecca fiorentina, Parmigiano stagionato"

    # 4. Rossi leggeri -> primi saporiti, salumi, carni bianche.
    if is_red:
        return "Tagliatelle al ragu, tagliere di salumi, pollo arrosto, pecorino semi-stagionato"

    # 5. Bianchi secchi con acidita alta -> fritti e piatti grassi (sgrassano).
    if not is_red and acidity >= 7:
        return "Fritto misto di pesce, spaghetti alle vongole, mozzarella di bufala, aperitivo"

    # 6. Bianchi secchi corposi -> pesce strutturato, crostacei, risotti.
    if not is_red and alcohol >= 12:
        return "Branzino al forno, risotto ai frutti di mare, astice, pollo al limone"

    # 7. Bianchi secchi leggeri (default) -> antipasti, pesce delicato, verdure.
    return "Antipasti di verdure, orata al vapore, insalata di mare, ricotta fresca"


def sql_escape(s: str) -> str:
    """Raddoppia gli apostrofi per l'inserimento sicuro in SQL."""
    return s.replace("'", "''")


def main() -> None:
    """Genera il file SQL con gli abbinamenti di tutti i lotti."""
    df = pd.read_csv(CSV).reset_index(drop=True)
    df.columns = [c.replace(" ", "_") for c in df.columns]
    df["id"] = df.index + 1  # stesso ordine di generate_seed.py

    rows = [(int(r["id"]), pairing_for(r)) for _, r in df.iterrows()]

    with open(OUT, "w") as f:
        f.write("-- Abbinamento cibo-vino generato da src/pairing.py con regole "
                "enologiche (contrapposizione/concordanza). Vedi dichiarazione etica.\n")
        f.write("ALTER TABLE wines ADD COLUMN food_pairing VARCHAR(200) NULL;\n\n")

        for start in range(0, len(rows), BATCH):
            chunk = rows[start:start + BATCH]
            cases = " ".join(f"WHEN {i} THEN '{sql_escape(p)}'" for i, p in chunk)
            ids = ",".join(str(i) for i, p in chunk)
            f.write(f"UPDATE wines SET food_pairing = CASE id {cases} END WHERE id IN ({ids});\n")

    print(f"OK: migrazione scritta in {OUT} ({len(rows)} vini)")


if __name__ == "__main__":
    main()
