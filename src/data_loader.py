"""Scarica e unisce il Wine Quality Dataset (UCI ML Repository, Cortez et al. 2009).

Il dataset originale e' distribuito in due file separati (vini rossi e bianchi),
ciascuno con le stesse 11 feature chimiche piu il punteggio di qualita (target).
Questo script li unisce in un unico CSV aggiungendo una colonna "type" per
distinguerli, cosi da poter addestrare un unico modello su entrambe le tipologie.
"""
from pathlib import Path
import pandas as pd

# URL ufficiali del dataset sul repository UCI (dati pubblici, licenza aperta)
URLS = {
    "red": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv",
    "white": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-white.csv",
}


def load_dataset(out_path: str = "data/wine_quality_merged.csv") -> pd.DataFrame:
    """Scarica entrambi i CSV UCI, li unisce e salva il risultato su disco.

    Args:
        out_path: percorso dove salvare il CSV unificato.

    Returns:
        DataFrame con tutti i vini (rossi + bianchi) e la colonna "type".

    Raises:
        RuntimeError: se il download di uno dei due file fallisce (es. rete
            assente o URL UCI cambiato).
    """
    frames = []
    for wine_type, url in URLS.items():
        try:
            df = pd.read_csv(url, sep=";")
        except Exception as e:
            raise RuntimeError(f"Download fallito per {wine_type}: {e}") from e
        df["type"] = wine_type
        frames.append(df)

    df = pd.concat(frames, ignore_index=True)
    # Normalizza i nomi colonna (il CSV UCI usa spazi, es. "fixed acidity")
    df.columns = [c.replace(" ", "_") for c in df.columns]

    Path("data").mkdir(exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"OK: {len(df)} vini salvati in {out_path}")
    return df


if __name__ == "__main__":
    load_dataset()
