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
        """Carica tutti i vini dal database, con le feature gia in float."""
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, type, " + ", ".join(FEATURES) + ", quality FROM wines")
            df = pd.DataFrame(cur.fetchall(), columns=[c[0] for c in cur.description])
            cur.close()
        df[FEATURES] = df[FEATURES].astype(float)
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
            ["id", "type", "alcohol", "ph", "residual_sugar", "quality", "similarity"]]


if __name__ == "__main__":
    # Test manuale rapido: raccomanda vini simili al primo vino del catalogo.
    rec = WineRecommender()
    wine = rec.df.iloc[0]
    print(f"Vino di partenza: id={wine['id']} ({wine['type']}, "
          f"alcol {wine['alcohol']}%, qualita {wine['quality']})\n")
    print(rec.recommend(int(wine["id"])).to_string(index=False))
