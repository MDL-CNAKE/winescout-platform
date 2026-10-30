"""Vista di magazzino: il catalogo ordinato per rischio di conservazione.

Risponde alla domanda commerciale di una piccola cantina — quali bottiglie
posso tenere e quali devo far uscire adesso — che il punteggio di qualita'
da solo non risolve: i due valori sono quasi scorrelati (0,16 sul catalogo).
"""
import pandas as pd
import streamlit as st

from src.ui import api, routing, stile
from src.ui.api import ApiError
from src.ui.formato import lotto_vino, tipo_esteso, titolo_vino


def pagina() -> None:
    st.title("Conservazione del magazzino")
    st.markdown(
        "I lotti più esposti in cima: quelli da immettere sul mercato prima che il tempo "
        "lavori contro di loro. Per gli indicatori di un singolo lotto apri la sua scheda."
    )

    c1, c2 = st.columns([1, 2])
    tipo = c1.segmented_control("Tipo", ["Tutti", "Rossi", "Bianchi"], default="Tutti",
                                key="cons_tipo") or "Tutti"
    limite = c2.select_slider("Quanti lotti mostrare", options=[20, 60, 100, 200], value=60,
                              key="cons_limite")

    try:
        righe = api.conservazione_lista({"Rossi": "red", "Bianchi": "white"}.get(tipo), limite)
    except ApiError as e:
        stile.errore(e)
        return

    tabella = pd.DataFrame([{
        "id": r["id"],
        "Referenza": titolo_vino(r["name"]),
        "Lotto": lotto_vino(r["name"]),
        "Tipo": tipo_esteso(r["type"]),
        "Qualità": r["quality"],
        "Prezzo": r["price_eur"],
        "Indice": r["punteggio"],
        "Indicazione": r["giudizio"],
    } for r in righe])

    versione = st.session_state.get("cons_versione", 0)
    evento = st.dataframe(
        tabella, hide_index=True, width="stretch", height=520,
        on_select="rerun", selection_mode="single-row", key=f"cons_tabella_{versione}",
        column_order=[c for c in tabella.columns if c != "id"],
        column_config={
            "Qualità": st.column_config.NumberColumn(format="%d/10"),
            "Prezzo": st.column_config.NumberColumn(format="%.2f €"),
            "Indice": st.column_config.ProgressColumn(format="%d", min_value=0, max_value=100),
        },
    )
    if evento.selection.rows:
        st.session_state["cons_versione"] = versione + 1
        routing.apri_vino(int(tabella.iloc[evento.selection.rows[0]]["id"]))

    st.caption("Indice 0-100: sotto 45 da immettere sul mercato, da 45 a 74 con monitoraggio, "
               "da 75 adatto alla conservazione.")
    stile.nota(stile.NOTA_CONSERVAZIONE)
