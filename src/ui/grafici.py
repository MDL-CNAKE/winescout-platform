"""Grafici Altair nei colori del marchio, condivisi fra le pagine.

Regola comune: il valore e' scritto sulla barra. In una presentazione chi
guarda non legge l'asse, e un numero da stimare a occhio non e' un dato.
"""
import altair as alt
import pandas as pd

ORO = "#e7d3a3"
BORDEAUX = "#a8394f"
CREMA = "#f4ece2"

# Colori fissi per tipo: un rosso deve restare bordeaux in ogni grafico.
COLORI_TIPO = alt.Scale(domain=["Rosso", "Bianco"], range=[BORDEAUX, ORO])


def barre(dati: pd.DataFrame, x: str, y: str, colore: str | None = None,
          orizzontale: bool = False, formato: str = ".3f", altezza: int = 220) -> alt.Chart:
    """Barre semplici o affiancate (con `colore`), con il valore sulla barra."""
    asse_valore = alt.X if orizzontale else alt.Y
    asse_categoria = alt.Y if orizzontale else alt.X
    codifica = {
        ("x" if orizzontale else "y"): asse_valore(f"{y}:Q", title=None, axis=alt.Axis(grid=False)),
        ("y" if orizzontale else "x"): asse_categoria(f"{x}:N", title=None, sort=None,
                                                       axis=alt.Axis(labelAngle=0, labelLimit=260)),
    }
    if colore:
        codifica["color"] = alt.Color(f"{colore}:N", title=None,
                                      scale=alt.Scale(range=[BORDEAUX, ORO]),
                                      legend=alt.Legend(orient="top"))
        if not orizzontale:
            codifica["xOffset"] = alt.XOffset(f"{colore}:N")
    else:
        codifica["color"] = alt.value(ORO)
    base = alt.Chart(dati).mark_bar(cornerRadius=3).encode(**codifica)
    testo = base.mark_text(
        align="left" if orizzontale else "center", baseline="middle" if orizzontale else "bottom",
        dx=4 if orizzontale else 0, dy=0 if orizzontale else -4, color=CREMA,
    ).encode(text=alt.Text(f"{y}:Q", format=formato))
    return (base + testo).properties(height=altezza)


def barre_per_tipo(dati: pd.DataFrame, categoria: str, valore: str = "Lotti",
                   altezza: int = 240) -> alt.Chart:
    """Barre impilate rossi/bianchi, con il totale sopra ogni colonna."""
    base = alt.Chart(dati).encode(
        x=alt.X(f"{categoria}:N", title=None, sort=None, axis=alt.Axis(labelAngle=0)),
    )
    pile = base.mark_bar(cornerRadius=2).encode(
        y=alt.Y(f"sum({valore}):Q", title=None, axis=alt.Axis(grid=False)),
        color=alt.Color("Tipo:N", title=None, scale=COLORI_TIPO, legend=alt.Legend(orient="top")),
        tooltip=[categoria, "Tipo", valore],
    )
    totali = base.mark_text(dy=-6, color=CREMA).encode(
        y=alt.Y(f"sum({valore}):Q"), text=alt.Text(f"sum({valore}):Q", format=","),
    )
    return (pile + totali).properties(height=altezza)


def mappa_calore(dati: pd.DataFrame, x: str, y: str, valore: str = "Lotti",
                 altezza: int = 260) -> alt.Chart:
    """Mappa a celle: quanti lotti per combinazione di due categorie."""
    base = alt.Chart(dati).encode(
        x=alt.X(f"{x}:N", title=None, sort=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y(f"{y}:N", title=None, sort="descending"),
    )
    celle = base.mark_rect(cornerRadius=3).encode(
        color=alt.Color(f"{valore}:Q", title=None,
                        scale=alt.Scale(range=["#2a1219", BORDEAUX, ORO]), legend=None),
        tooltip=[x, y, valore],
    )
    numeri = base.mark_text(fontSize=11).encode(
        text=alt.Text(f"{valore}:Q", format=","),
        color=alt.condition(f"datum['{valore}'] > 0", alt.value(CREMA), alt.value("transparent")),
    )
    return (celle + numeri).properties(height=altezza)
