"""Scarica e unisce il Wine Quality Dataset (UCI, Cortez et al.)."""
from pathlib import Path
import pandas as pd

URLS = {
    "red": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv",
    "white": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-white.csv",
}

def load_dataset(out_path: str = "data/wine_quality_merged.csv") -> pd.DataFrame:
    frames = []
    for wine_type, url in URLS.items():
        try:
            df = pd.read_csv(url, sep=";")
        except Exception as e:
            raise RuntimeError(f"Download fallito per {wine_type}: {e}") from e
        df["type"] = wine_type
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df.columns = [c.replace(" ", "_") for c in df.columns]
    Path("data").mkdir(exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"OK: {len(df)} vini salvati in {out_path}")
    return df

if __name__ == "__main__":
    load_dataset()
