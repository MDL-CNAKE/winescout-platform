"""Packaging suggerito per ogni lotto: stile, formato, tappo, etichetta.

Le regole stanno nel backend (backend/main.py, funzioni _packaging_style,
_bottle_format, _cap_type): qui si filtrano e si riassumono.
"""
import pandas as pd
import streamlit as st

from src.ui import api, routing, stile
from src.ui.api import ApiError
from src.ui.formato import lotto_vino, tipo_esteso, titolo_vino


def pagina() -> None:
    st.title("Packaging")
    st.markdown("Come confezionare ogni lotto, in base a qualità e prezzo.")

    try:
        dati = pd.DataFrame(api.packaging_lista())
    except ApiError as e:
        stile.errore(e)
        return

    c1, c2, c3 = st.columns(3)
    stili = c1.multiselect("Stile", sorted(dati["style"].unique()), key="pack_stili")
    tappi = c2.multiselect("Tappo", sorted(dati["cap_type"].unique()), key="pack_tappi")
    tipo = c3.segmented_control("Tipo", ["Tutti", "Rossi", "Bianchi"], default="Tutti",
                                key="pack_tipo") or "Tutti"

    filtrati = dati
    if stili:
        filtrati = filtrati[filtrati["style"].isin(stili)]
    if tappi:
        filtrati = filtrati[filtrati["cap_type"].isin(tappi)]
    if tipo != "Tutti":
        filtrati = filtrati[filtrati["type"] == ("red" if tipo == "Rossi" else "white")]

    conteggi = filtrati["style"].value_counts()
    colonne = st.columns(max(1, len(conteggi)))
    for colonna, (nome, n) in zip(colonne, conteggi.items()):
        colonna.metric(nome, f"{n} lotti", border=True)

    tabella = pd.DataFrame({
        "id": filtrati["id"],
        "Referenza": filtrati["name"].map(titolo_vino),
        "Lotto": filtrati["name"].map(lotto_vino),
        "Tipo": filtrati["type"].map(tipo_esteso),
        "Qualità": filtrati["quality"],
        "Prezzo": filtrati["price_eur"],
        "Stile": filtrati["style"],
        "Formato": filtrati["bottle_format"],
        "Tappo": filtrati["cap_type"],
        "Etichetta": filtrati["label_material"],
    }).reset_index(drop=True)

    versione = st.session_state.get("pack_versione", 0)
    evento = st.dataframe(
        tabella, hide_index=True, width="stretch", height=480,
        on_select="rerun", selection_mode="single-row", key=f"pack_tabella_{versione}",
        column_order=[c for c in tabella.columns if c != "id"],
        column_config={
            "Qualità": st.column_config.NumberColumn(format="%d/10"),
            "Prezzo": st.column_config.NumberColumn(format="%.2f €"),
        },
    )
    if evento.selection.rows:
        st.session_state["pack_versione"] = versione + 1
        routing.apri_vino(int(tabella.iloc[evento.selection.rows[0]]["id"]))

    stile.nota(
        "<strong>Come sono scelte.</strong> Il tappo segue la qualità, cioè la durata prevista "
        "del vino, non il colore: sughero naturale solo da qualità 7 in su, dove c'è qualcosa da "
        "far evolvere; sintetico per la fascia media; vite per il consumo immediato. Una regola "
        "precedente dava il sughero a ogni rosso, anche di qualità 3 su una mignon: la chiusura "
        "più costosa sulla confezione più economica. Nessun criterio usa la menzione 'Riserva', "
        "che per legge richiede un affinamento che il dataset non documenta."
    )
