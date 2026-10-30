"""Catalogo: filtri, ordinamento, paginazione ed export CSV.

Filtri e ordinamento sono parametri dell'API, non lavoro dell'interfaccia:
con 6.497 vini scaricarli tutti per mostrarne una pagina sarebbe uno spreco,
e ogni cambio di filtro rifa' la query lato database.
"""
import math

import pandas as pd
import streamlit as st

from src.ui import api, routing, stile
from src.ui.api import ApiError
from src.ui.formato import lotto_vino, tipo_esteso, titolo_vino

PER_PAGINA = 50

ORDINAMENTI = {
    "quality_desc": "Qualità, dalla più alta",
    "quality_asc": "Qualità, dalla più bassa",
    "price_asc": "Prezzo crescente",
    "price_desc": "Prezzo decrescente",
    "alcohol_desc": "Gradazione, dalla più alta",
    "name_asc": "Nome",
}


def _intervallo(etichetta: str, minimo: float, massimo: float, passo: float,
                chiave: str) -> tuple[float | None, float | None]:
    """Slider di intervallo che restituisce None sugli estremi.

    Un estremo lasciato al suo valore massimo non e' un filtro: mandarlo al
    backend aggiungerebbe una condizione inutile alla query.
    """
    basso, alto = st.slider(etichetta, minimo, massimo, (minimo, massimo), step=passo, key=chiave)
    return (basso if basso > minimo else None, alto if alto < massimo else None)


def _filtri() -> tuple[dict, str]:
    f = api.intervalli()
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            tipo = st.segmented_control("Tipo", ["Tutti", "Rossi", "Bianchi"], default="Tutti",
                                        key="cat_tipo")
            q_min, q_max = f["quality"]
            qualita = st.select_slider("Qualità minima", options=list(range(q_min, q_max + 1)),
                                       value=q_min, key="cat_qualita")
        with c2:
            prezzo = _intervallo("Prezzo (€)", float(math.floor(f["price_eur"][0])),
                                 float(math.ceil(f["price_eur"][1])), 0.5, "cat_prezzo")
            alcol = _intervallo("Alcol (% vol)", float(math.floor(f["alcohol"][0])),
                                float(math.ceil(f["alcohol"][1])), 0.1, "cat_alcol")
        with c3:
            zucchero = _intervallo("Zucchero residuo (g/L)", float(math.floor(f["residual_sugar"][0])),
                                   float(math.ceil(f["residual_sugar"][1])), 0.5, "cat_zucchero")
            acidita = _intervallo("Acidità fissa (g/L)", float(math.floor(f["fixed_acidity"][0])),
                                  float(math.ceil(f["fixed_acidity"][1])), 0.1, "cat_acidita")
            ordine = st.selectbox("Ordina per", list(ORDINAMENTI), format_func=ORDINAMENTI.get,
                                  key="cat_ordine")

    filtri = {
        "type": {"Rossi": "red", "Bianchi": "white"}.get(tipo or "Tutti"),
        "min_quality": qualita if qualita > q_min else None,
        "min_price": prezzo[0], "max_price": prezzo[1],
        "min_alcohol": alcol[0], "max_alcohol": alcol[1],
        "min_sugar": zucchero[0], "max_sugar": zucchero[1],
        "min_acidity": acidita[0], "max_acidity": acidita[1],
    }
    # Solo i filtri attivi: la chiave della cache resta stabile e la query
    # contiene solo le condizioni che servono.
    return {k: v for k, v in filtri.items() if v is not None}, ordine


def _pagina_corrente(firma: tuple) -> int:
    """Cambiare filtri riporta alla prima pagina: restare alla 12 dopo aver
    ristretto a 30 risultati mostrerebbe una pagina vuota."""
    if st.session_state.get("cat_firma") != firma:
        st.session_state["cat_firma"] = firma
        st.session_state["cat_pagina"] = 1
    return st.session_state.get("cat_pagina", 1)


def _export(filtri: dict, ordine: str, totale: int) -> None:
    """Export in due passi: il file si scarica solo quando serve, non a ogni
    esecuzione della pagina."""
    firma = (tuple(sorted(filtri.items())), ordine)
    c1, c2, c3 = st.columns([1.3, 1.3, 3])
    formato = c1.segmented_control(
        "Formato CSV", ["it", "en"], default="it", key="cat_formato",
        format_func={"it": "Excel italiano", "en": "Internazionale"}.get,
    ) or "it"
    if c2.button(f"Prepara CSV ({totale} referenze)", width="stretch"):
        try:
            st.session_state["cat_export"] = (firma, formato, api.esporta_csv(filtri, ordine, formato))
        except ApiError as e:
            stile.errore(e)

    pronto = st.session_state.get("cat_export")
    if pronto and pronto[0] == firma and pronto[1] == formato:
        c2.download_button("Scarica il file", data=pronto[2], mime="text/csv",
                           file_name="catalogo_cruscout.csv", type="primary", width="stretch")
    c3.caption(
        "Esporta tutte le referenze filtrate, non solo la pagina a schermo. "
        "'Excel italiano' usa il punto e virgola e la virgola decimale; "
        "'Internazionale' è per Power Query e pandas."
    )


def pagina() -> None:
    st.title("Catalogo")
    st.caption("Seleziona una riga per aprire la scheda del vino.")

    try:
        filtri, ordine = _filtri()
        pag = _pagina_corrente((tuple(sorted(filtri.items())), ordine))
        risultato = api.cerca_vini(filtri, ordine, pag, PER_PAGINA)
    except ApiError as e:
        stile.errore(e)
        return

    totale = risultato["total"]
    if totale == 0:
        st.info("Nessuna referenza con questi criteri. Allarga gli intervalli o azzera i filtri.")
        return

    _export(filtri, ordine, totale)

    righe = pd.DataFrame([{
        "id": v["id"],
        "Referenza": titolo_vino(v["name"]),
        "Lotto": lotto_vino(v["name"]),
        "Tipo": tipo_esteso(v["type"]),
        "Qualità": v["quality"],
        "Alcol": v["alcohol"],
        "pH": v["ph"],
        "Zucchero": v["residual_sugar"],
        "Prezzo": v["price_eur"],
        "Margine %": v["margin_pct"],
        "Abbinamento": v["food_pairing"],
    } for v in risultato["items"]])

    # La chiave cambia dopo ogni apertura: senza, tornando al catalogo la
    # riga risulterebbe ancora selezionata e riaprirebbe subito la scheda.
    versione = st.session_state.get("cat_versione", 0)
    evento = st.dataframe(
        righe, hide_index=True, width="stretch", height=560,
        on_select="rerun", selection_mode="single-row", key=f"cat_tabella_{versione}",
        column_order=[c for c in righe.columns if c != "id"],
        column_config={
            "Qualità": st.column_config.NumberColumn(format="%d/10"),
            "Alcol": st.column_config.NumberColumn(format="%.1f%%"),
            "pH": st.column_config.NumberColumn(format="%.2f"),
            "Zucchero": st.column_config.NumberColumn(format="%.1f g/L"),
            "Prezzo": st.column_config.NumberColumn(format="%.2f €"),
            "Margine %": st.column_config.NumberColumn(format="%.1f%%"),
            "Abbinamento": st.column_config.TextColumn(width="large"),
        },
    )
    if evento.selection.rows:
        st.session_state["cat_versione"] = versione + 1
        routing.apri_vino(int(righe.iloc[evento.selection.rows[0]]["id"]))

    pagine_totali = max(1, math.ceil(totale / PER_PAGINA))
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("← Precedente", disabled=pag <= 1, width="stretch"):
        st.session_state["cat_pagina"] = pag - 1
        st.rerun()
    c2.markdown(
        f"<p style='text-align:center;margin-top:.4rem'>Pagina {pag} di {pagine_totali} · "
        f"{totale} referenze</p>", unsafe_allow_html=True,
    )
    if c3.button("Successiva →", disabled=pag >= pagine_totali, width="stretch"):
        st.session_state["cat_pagina"] = pag + 1
        st.rerun()

    stile.nota(stile.NOTA_SIMULATI)

    m1, m2, m3 = st.columns(3)
    m1.metric("Vini analizzati", "6.497", border=True)
    m2.metric("Cross-validation raggruppata", "R² 0,39", border=True)
    m3.metric("Test set senza righe ripetute", "R² 0,40", border=True)
    st.caption("Dataset UCI Wine Quality · RandomForestRegressor in Pipeline scikit-learn")
