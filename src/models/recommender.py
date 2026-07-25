"""Motore di raccomandazione content-based basato su similarita coseno.

Approccio: ogni vino e' rappresentato come un vettore delle sue 11 feature
chimiche (standardizzate). La similarita coseno tra due vettori misura quanto
i due vini sono "chimicamente vicini" indipendentemente dalla loro scala
assoluta: e' la tecnica indicata esplicitamente nella traccia del progetto
("Regressione e raccomandazione con similarita coseno").
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

from src.database.connection import DatabaseConnection

FEATURES = ["fixed_acidity", "volatile_acidity", "citric_acid", "residual_sugar",
            "chlorides", "free_sulfur_dioxide", "total_sulfur_dioxide",
            "density", "ph", "sulphates", "alcohol"]


class WineRecommender:
    """Raccomanda vini chimicamente simili a un vino dato.

    La matrice di similarita (6497x6497) viene calcolata una sola volta alla
    creazione dell'istanza e riusata per ogni chiamata a recommend(): per
    questo motivo l'app Streamlit la mantiene in cache con
    @st.cache_resource invece di ricrearla a ogni interazione dell'utente.
    """

    def __init__(self) -> None:
        self.df = self._load()
        # StandardScaler e' necessario perche le feature hanno scale molto
        # diverse (es. total_sulfur_dioxide arriva a centinaia, il pH resta
        # tra 2.7 e 4.0): senza standardizzazione la similarita sarebbe
        # dominata dalle feature con valori piu grandi in valore assoluto.
        scaled = StandardScaler().fit_transform(self.df[FEATURES])
        self.similarity = cosine_similarity(scaled)

    @staticmethod
    def _load() -> pd.DataFrame:
        """Carica tutti i vini dal database, con le feature gia in float.

        Include anche name e price_eur (aggiunti dalle migrazioni V3/V4):
        non servono al calcolo della similarita chimica, ma servono a
        find_cheaper_alternative() per confrontare i prezzi.
        """
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, name, type, price_eur, food_pairing, " + ", ".join(FEATURES) + ", quality FROM wines"
            )
            df = pd.DataFrame(cur.fetchall(), columns=[c[0] for c in cur.description])
            cur.close()
        df[FEATURES] = df[FEATURES].astype(float)
        # MySQL restituisce le colonne DECIMAL come Decimal di Python, non
        # float: senza questo cast le operazioni aritmetiche in
        # find_cheaper_alternative() falliscono con TypeError.
        df["price_eur"] = df["price_eur"].astype(float)
        return df

    def recommend(self, wine_id: int, top_n: int = 5, same_type: bool = True) -> pd.DataFrame:
        """Restituisce i top_n vini piu simili a wine_id.

        Args:
            wine_id: id del vino di partenza (colonna `id` della tabella wines).
            top_n: numero di raccomandazioni da restituire.
            same_type: se True, raccomanda solo vini dello stesso tipo
                (rosso con rosso, bianco con bianco) - ha piu senso per un
                utente che vuole un'alternativa simile, non un vino diverso
                per categoria.

        Returns:
            DataFrame con i vini raccomandati e il relativo punteggio di
            similarita (1.0 = identico, 0.0 = nessuna correlazione).

        Raises:
            ValueError: se wine_id non esiste nel catalogo.
        """
        matches = self.df.index[self.df["id"] == wine_id]
        if len(matches) == 0:
            raise ValueError(f"Vino con id={wine_id} non trovato nel catalogo")

        idx = matches[0]
        result = self.df.copy()
        result["similarity"] = self.similarity[idx]
        result = result[result["id"] != wine_id]  # escludi il vino stesso
        if same_type:
            result = result[result["type"] == self.df.loc[idx, "type"]]

        return result.nlargest(top_n, "similarity")[
            ["id", "name", "type", "alcohol", "ph", "residual_sugar", "quality", "price_eur", "similarity"]]


    def find_cheaper_alternative(self, wine_id: int, max_candidates: int = 10) -> pd.DataFrame:
        """Trova un'alternativa piu economica ma chimicamente simile.

        Caso d'uso reale per un ristoratore/responsabile acquisti: "questo
        vino sta per finire o e' troppo caro, qual e' il sostituto piu
        simile che costa meno?". Cerca tra i piu simili (coseno) quelli con
        prezzo inferiore al vino di partenza, e li ordina per il miglior
        compromesso similarita/risparmio.

        Args:
            wine_id: id del vino da sostituire.
            max_candidates: quanti vini simili considerare prima di filtrare
                per prezzo (piu alto = ricerca piu ampia ma piu lenta).

        Returns:
            DataFrame con le alternative piu economiche trovate, ordinate
            per punteggio combinato (similarita alta + risparmio alto),
            oppure DataFrame vuoto se non esistono alternative piu economiche
            tra i vini simili.

        Raises:
            ValueError: se wine_id non esiste nel catalogo.
        """
        matches = self.df.index[self.df["id"] == wine_id]
        if len(matches) == 0:
            raise ValueError(f"Vino con id={wine_id} non trovato nel catalogo")

        base_price = float(self.df.loc[matches[0], "price_eur"])
        candidates = self.recommend(wine_id, top_n=max_candidates, same_type=True)
        cheaper = candidates[candidates["price_eur"] < base_price].copy()

        if cheaper.empty:
            return cheaper

        # Punteggio combinato: 70% peso alla similarita chimica, 30% al
        # risparmio percentuale. Pesi scelti per privilegiare la coerenza
        # del profilo gustativo rispetto al solo risparmio economico.
        cheaper["savings_pct"] = (base_price - cheaper["price_eur"]) / base_price
        cheaper["score"] = 0.7 * cheaper["similarity"] + 0.3 * cheaper["savings_pct"]

        return cheaper.sort_values("score", ascending=False)


if __name__ == "__main__":
    # Test manuale rapido: raccomanda vini simili al primo vino del catalogo.
    rec = WineRecommender()
    wine = rec.df.iloc[0]
    print(f"Vino di partenza: id={wine['id']} ({wine['type']}, "
          f"alcol {wine['alcohol']}%, qualita {wine['quality']})\n")
    print(rec.recommend(int(wine["id"])).to_string(index=False))
