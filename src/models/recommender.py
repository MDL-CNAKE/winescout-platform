"""Motore di raccomandazione content-based con similarita coseno."""
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
    """Raccomanda vini chimicamente simili a un vino dato (similarita coseno)."""

    def __init__(self) -> None:
        self.df = self._load()
        scaled = StandardScaler().fit_transform(self.df[FEATURES])
        self.similarity = cosine_similarity(scaled)

    @staticmethod
    def _load() -> pd.DataFrame:
        with DatabaseConnection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, type, " + ", ".join(FEATURES) + ", quality FROM wines")
            df = pd.DataFrame(cur.fetchall(), columns=[c[0] for c in cur.description])
            cur.close()
        df[FEATURES] = df[FEATURES].astype(float)
        return df

    def recommend(self, wine_id: int, top_n: int = 5, same_type: bool = True) -> pd.DataFrame:
        """Restituisce i top_n vini piu simili a wine_id (esclude il vino stesso)."""
        matches = self.df.index[self.df["id"] == wine_id]
        if len(matches) == 0:
            raise ValueError(f"Vino con id={wine_id} non trovato nel catalogo")
        idx = matches[0]
        result = self.df.copy()
        result["similarity"] = self.similarity[idx]
        result = result[result["id"] != wine_id]
        if same_type:
            result = result[result["type"] == self.df.loc[idx, "type"]]
        return result.nlargest(top_n, "similarity")[
            ["id", "type", "alcohol", "ph", "residual_sugar", "quality", "similarity"]]


if __name__ == "__main__":
    rec = WineRecommender()
    wine = rec.df.iloc[0]
    print(f"Vino di partenza: id={wine['id']} ({wine['type']}, "
          f"alcol {wine['alcohol']}%, qualita {wine['quality']})\n")
    print(rec.recommend(int(wine["id"])).to_string(index=False))
