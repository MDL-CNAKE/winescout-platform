"""Catalogo: filtri, ordinamento, paginazione ed export CSV.

Filtri e ordinamento sono parametri dell'API, non lavoro dell'interfaccia:
con 6.497 vini scaricarli tutti per mostrarne una pagina sarebbe uno spreco,
e ogni cambio di filtro rifa' la query lato database.

Due viste sugli stessi risultati: la griglia di card, come nel frontend
React, per chi sceglie un vino; la tabella per chi confronta valori.
"""
import html
import math

import pandas as pd
import streamlit as st

from src.ui import api, routing, stile
from src.ui.api import ApiError
from src.ui.disegni import bottiglia
from src.ui.formato import descrizione_card, euro, iniziali, lotto_vino, tipo_esteso, titolo_vino

# Per vista: la griglia mostra meno vini per pagina perche' ogni card occupa
# molto piu' spazio di una riga.
PER_PAGINA = {"griglia": 24, "tabella": 50}
COLONNE_GRIGLIA = 4

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


def _card_html(v: dict, colleghi: list[str]) -> str:
    """Card di un vino: bottiglia, lotto, colleghi, titolo, descrizione, prezzo.

    Tutto il testo e' escapato: nomi e abbinamenti arrivano dal database e
    vengono inseriti in HTML.
    """
    lotto = lotto_vino(v["name"])
    etichetta = f"Lotto {lotto}" if lotto else tipo_esteso(v["type"])
    segni = "".join(f"<span>{html.escape(iniziali(n))}</span>" for n in colleghi[:3])
    if len(colleghi) > 3:
        segni += f"<span>+{len(colleghi) - 3}</span>"
    titolo_colleghi = html.escape("Segnato da: " + ", ".join(colleghi)) if colleghi else ""
    figura = bottiglia(v["id"], v["type"], v["quality"], v["alcohol"], v["residual_sugar"], altezza=150)
    return (
        f'<div class="card-figura">{figura}</div>'
        f'<div class="card-riga"><span class="card-lotto">{etichetta}</span>'
        f'<span class="card-colleghi" title="{titolo_colleghi}">{segni}</span></div>'
        f'<p class="card-titolo">{html.escape(titolo_vino(v["name"]))}</p>'
        f'<p class="card-desc">{html.escape(descrizione_card(v))}</p>'
        f'<span class="card-prezzo">{euro(v["price_eur"])}</span>'
    )


def _griglia(vini: list[dict]) -> None:
    operatore = st.session_state.get(routing.OPERATORE)
    try:
        segnati = api.preferiti()
    except ApiError:
        segnati = []

    for inizio in range(0, len(vini), COLONNE_GRIGLIA):
        colonne = st.columns(COLONNE_GRIGLIA)
        for colonna, v in zip(colonne, vini[inizio:inizio + COLONNE_GRIGLIA]):
            di_questo = [p for p in segnati if p["wine_id"] == v["id"]]
            mio = any(p["operator_id"] == operatore for p in di_questo)
            colleghi = [p["operator_name"] for p in di_questo if p["operator_id"] != operatore]
            with colonna.container(border=True):
                stile.html(_card_html(v, colleghi))
                c1, c2 = st.columns([3, 1])
                if c1.button("Scopri", key=f"scopri_{v['id']}", type="primary", width="stretch"):
                    routing.apri_vino(v["id"])
                if operatore is not None and c2.button(
                    "", icon=":material/favorite:", key=f"segna_{v['id']}",
                    type="primary" if mio else "secondary", width="stretch",
                    help="Togli dalla mia selezione" if mio else "Aggiungi alla mia selezione",
                ):
                    try:
                        if mio:
                            api.rimuovi_preferito(v["id"], operatore)
                        else:
                            api.aggiungi_preferito(v["id"], operatore)
                    except ApiError as e:
                        stile.errore(e)
                        return
                    st.rerun()


def _tabella(vini: list[dict]) -> None:
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
    } for v in vini])

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


def _paginazione(pag: int, totale: int, per_pagina: int) -> None:
    pagine_totali = max(1, math.ceil(totale / per_pagina))
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


def pagina() -> None:
    c1, c2 = st.columns([3, 1])
    c1.title("Catalogo")
    vista = c2.segmented_control("Vista", ["griglia", "tabella"], default="griglia",
                                 key="cat_vista", label_visibility="collapsed",
                                 format_func={"griglia": "Griglia", "tabella": "Tabella"}.get) or "griglia"

    try:
        filtri, ordine = _filtri()
        pag = _pagina_corrente((tuple(sorted(filtri.items())), ordine, vista))
        risultato = api.cerca_vini(filtri, ordine, pag, PER_PAGINA[vista])
    except ApiError as e:
        stile.errore(e)
        return

    totale = risultato["total"]
    if totale == 0:
        st.info("Nessuna referenza con questi criteri. Allarga gli intervalli o azzera i filtri.")
        return

    _export(filtri, ordine, totale)

    if vista == "griglia":
        _griglia(risultato["items"])
    else:
        st.caption("Seleziona una riga per aprire la scheda del vino.")
        _tabella(risultato["items"])

    _paginazione(pag, totale, PER_PAGINA[vista])

    stile.nota(stile.NOTA_SIMULATI)
    stile.html(
        '<div class="fascia">'
        '<div><b>6.497</b><span>vini analizzati</span></div>'
        '<div><b>5-fold</b><span>cross-validation raggruppata · R² 0,39</span></div>'
        '<div><b>R² 0,40</b><span>su test set senza righe ripetute</span></div>'
        '</div><p class="fascia-fonte">Dataset UCI Wine Quality · '
        'RandomForestRegressor con pipeline scikit-learn</p>'
    )


