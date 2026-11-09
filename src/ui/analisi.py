"""Aggregazioni del cruscotto vendite, senza dipendenze da Streamlit.

Lavorano solo sui dati che il catalogo contiene davvero: chimica, qualita',
tipo, e prezzo e margine simulati. Non esistono ordini, clienti ne' date di
vendita, quindi qui non c'e' nessun fatturato: inventarlo sarebbe lo stesso
errore che il progetto rifiuta per i vitigni.
"""
import pandas as pd

FASCE_PREZZO = [0, 10, 15, 20, 25, 30, float("inf")]
ETICHETTE_FASCE = ["< 10 €", "10–15 €", "15–20 €", "20–25 €", "25–30 €", "≥ 30 €"]


def prepara(vini: list[dict], tipo: str | None = None) -> pd.DataFrame:
    """Catalogo come tabella, con le colonne che servono ai grafici."""
    df = pd.DataFrame(vini)
    if df.empty:
        return df
    if tipo in ("red", "white"):
        df = df[df["type"] == tipo]
    df = df.dropna(subset=["price_eur", "margin_pct"]).copy()
    df["Tipo"] = df["type"].map({"red": "Rosso", "white": "Bianco"})
    df["Fascia"] = pd.cut(df["price_eur"], FASCE_PREZZO, labels=ETICHETTE_FASCE, right=False)
    df["Margine €"] = df["price_eur"] * df["margin_pct"] / 100
    return df


def indicatori(df: pd.DataFrame) -> dict:
    """Valori della riga di indicatori in alto."""
    if df.empty:
        return {"lotti": 0, "prezzo_medio": None, "margine_euro_medio": None, "margine_pct_medio": None}
    return {
        "lotti": len(df),
        "prezzo_medio": float(df["price_eur"].mean()),
        "margine_euro_medio": float(df["Margine €"].mean()),
        "margine_pct_medio": float(df["margin_pct"].mean()),
    }


def lotti_per(df: pd.DataFrame, colonna: str) -> pd.DataFrame:
    """Conteggio dei lotti per una categoria e per tipo, categorie vuote incluse."""
    conteggi = df.groupby([colonna, "Tipo"], observed=False).size().reset_index(name="Lotti")
    conteggi[colonna] = conteggi[colonna].astype(str)
    return conteggi


def margini_per_fascia(df: pd.DataFrame) -> pd.DataFrame:
    """Margine medio per fascia di prezzo, in percentuale e in euro.

    Le due colonne vanno in direzioni opposte: la percentuale scende al salire
    del prezzo, l'importo sale. E' il motivo per cui "spingi i margini
    migliori" e' un consiglio ambiguo finche' non si dice quale dei due.
    """
    gruppi = df.groupby("Fascia", observed=True).agg(
        **{"Margine %": ("margin_pct", "mean"), "Margine €": ("Margine €", "mean"),
           "Lotti": ("id", "count")}
    ).reset_index()
    gruppi["Fascia"] = gruppi["Fascia"].astype(str)
    return gruppi.round(2)


def qualita_per_fascia(df: pd.DataFrame) -> pd.DataFrame:
    """Lotti per qualita' e fascia di prezzo, per la mappa a celle."""
    tabella = df.groupby(["quality", "Fascia"], observed=False).size().reset_index(name="Lotti")
    tabella["Qualità"] = tabella["quality"].astype(int).astype(str)
    tabella["Fascia"] = tabella["Fascia"].astype(str)
    return tabella[["Qualità", "Fascia", "Lotti"]]
