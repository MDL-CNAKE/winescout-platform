"""Vendite: cruscotto del catalogo e profili di mercato.

CRUSCOTTO. Mostra solo cio' che il catalogo contiene: composizione per
prezzo, qualita' e tipo, margini (simulati, e dichiarati come tali), lotti da
far uscire per primi. Non c'e' fatturato ne' venduto: il database non ha un
solo ordine, e un grafico delle vendite sarebbe inventato. Chi vuole
analisi su misura scarica il CSV dal catalogo e lo collega a Power BI.

PROFILI. I profili li scrive chi vende: il dataset non contiene geografia,
clienti ne' storico vendite, quindi nulla permette di dedurre cosa piaccia a
un mercato. La conoscenza commerciale resta umana e viene dichiarata; il
sistema cerca fra 6.497 lotti quelli che vi rispondono.
"""
import pandas as pd
import streamlit as st

from src.ui import analisi, api, grafici, routing, stile
from src.ui.api import ApiError
from src.ui.formato import descrivi_criteri, euro, lotto_vino, titolo_vino

PROFILO_ATTIVO = "vendite_profilo"
SIMULATO = ":orange[simulato]"


def _cruscotto() -> None:
    tipo = st.segmented_control("Tipo", ["Tutti", "Rossi", "Bianchi"], default="Tutti",
                                key="vend_tipo", label_visibility="collapsed") or "Tutti"
    codice = {"Rossi": "red", "Bianchi": "white"}.get(tipo)

    try:
        with st.spinner("Preparo il cruscotto..."):
            df = analisi.prepara(api.catalogo_completo(), codice)
            riepilogo = api.conservazione_riepilogo()
    except ApiError as e:
        stile.errore(e)
        return
    if df.empty:
        st.info("Nessun lotto in catalogo.")
        return

    # --- Indicatori ---------------------------------------------------------
    k = analisi.indicatori(df)
    da_muovere = sum(r["lotti"] for r in riepilogo
                     if r["giudizio"] == "Da immettere sul mercato" and (codice is None or r["type"] == codice))
    c = st.columns(5)
    c[0].metric("Lotti in catalogo", f"{k['lotti']:,}".replace(",", "."), border=True)
    c[1].metric("Prezzo medio", euro(k["prezzo_medio"]), border=True, help="Prezzo simulato.")
    c[2].metric("Margine medio a bottiglia", euro(k["margine_euro_medio"]), border=True,
                help="Simulato: prezzo × margine %.")
    c[3].metric("Margine % medio", f"{k['margine_pct_medio']:.1f}%".replace(".", ","), border=True,
                help="Simulato.")
    c[4].metric("Da immettere subito", f"{da_muovere:,}".replace(",", "."), border=True,
                delta=f"{100 * da_muovere / k['lotti']:.1f}% dei lotti".replace(".", ","),
                delta_color="off", help="Dall'indice di conservazione: lotti poco protetti.")

    # --- Composizione (dati reali) -----------------------------------------
    st.subheader("Com'è fatta l'offerta")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Lotti per fascia di prezzo**")
        st.altair_chart(grafici.barre_per_tipo(analisi.lotti_per(df, "Fascia"), "Fascia"),
                        width="stretch")
    with c2:
        st.markdown("**Lotti per punteggio di qualità**")
        st.altair_chart(grafici.barre_per_tipo(analisi.lotti_per(df, "quality").rename(
            columns={"quality": "Qualità"}), "Qualità"), width="stretch")

    st.markdown("**Qualità e prezzo insieme**")
    st.altair_chart(grafici.mappa_calore(analisi.qualita_per_fascia(df), "Fascia", "Qualità"),
                    width="stretch")
    st.caption("Ogni cella conta i lotti con quel punteggio in quella fascia di prezzo. "
               "Le celle vuote sono combinazioni che il catalogo non offre.")

    # --- Margini (simulati) -------------------------------------------------
    st.subheader("Dove si guadagna")
    st.markdown(f"Margini {SIMULATO} con la logica di `src/pricing.py`: servono a leggere la "
                "struttura dell'offerta, non sono listini reali.")
    margini = analisi.margini_per_fascia(df)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Margine % medio per fascia**")
        st.altair_chart(grafici.barre(margini, "Fascia", "Margine %", formato=".1f"), width="stretch")
    with c2:
        st.markdown("**Margine € medio a bottiglia per fascia**")
        st.altair_chart(grafici.barre(margini, "Fascia", "Margine €", formato=".2f"), width="stretch")
    stile.nota(
        "<strong>I due margini vanno in direzioni opposte.</strong> La percentuale scende al "
        "salire del prezzo, l'importo in euro sale: una bottiglia da 12 € al 63% rende circa "
        "7,56 €, una da 24 € al 42% ne rende circa 10,08. 'Spingere i margini migliori' è un "
        "consiglio ambiguo finché non si dice quale dei due."
    )

    # --- Magazzino ----------------------------------------------------------
    st.subheader("Cosa far uscire per primo")
    cons = pd.DataFrame(riepilogo)
    if codice:
        cons = cons[cons["type"] == codice]
    cons["Tipo"] = cons["type"].map({"red": "Rosso", "white": "Bianco"})
    cons = cons.rename(columns={"giudizio": "Indicazione", "lotti": "Lotti"})
    st.altair_chart(grafici.barre_per_tipo(cons, "Indicazione", altezza=220), width="stretch")
    if "conservazione" in routing.PAGINE:
        st.page_link(routing.PAGINE["conservazione"], label="Vedi i lotti uno per uno",
                     icon=":material/schedule:")

    st.caption(
        "Fatturato, ordini, canali e stagionalità non compaiono perché il database non li "
        "contiene: la pagina Marketing indica quale dato servirebbe per ciascuno. Per analisi "
        "su misura scarica il CSV dal catalogo e collegalo a Power BI o Excel."
    )


def _nuovo_profilo() -> None:
    with st.expander("Nuovo profilo"):
        with st.form("nuovo_profilo", clear_on_submit=True):
            nome = st.text_input("Nome del profilo", max_chars=80,
                                 placeholder="Es: Nord Europa - bianchi freschi")
            note = st.text_input("Note", max_chars=300, placeholder="Cosa cerca questo canale, in una riga")
            tipo = st.segmented_control("Tipo", ["tutti", "red", "white"], default="tutti",
                                        format_func={"tutti": "Indifferente", "red": "Rossi",
                                                     "white": "Bianchi"}.get)
            c = st.columns(3)
            # value=None lascia il campo vuoto: un campo vuoto non filtra nulla,
            # invece di imporre un valore arbitrario.
            min_q = c[0].number_input("Qualità minima", 0, 10, value=None, step=1)
            min_a = c[1].number_input("Alcol minimo %", 0.0, 20.0, value=None, step=0.1)
            max_a = c[2].number_input("Alcol massimo %", 0.0, 20.0, value=None, step=0.1)
            max_z = c[0].number_input("Zucchero max g/L", 0.0, 70.0, value=None, step=0.5)
            min_ac = c[1].number_input("Acidità minima g/L", 0.0, 20.0, value=None, step=0.1)
            max_p = c[2].number_input("Prezzo massimo €", 0.0, 100.0, value=None, step=0.5)
            st.caption("I campi lasciati vuoti non filtrano nulla.")
            salva = st.form_submit_button("Salva profilo", type="primary")

        if salva:
            if not nome.strip():
                st.error("Il nome del profilo è obbligatorio.")
                return
            try:
                nuovo = api.crea_profilo({
                    "name": nome.strip(), "notes": note.strip() or None,
                    "wine_type": tipo if tipo in ("red", "white") else None,
                    "min_quality": min_q, "min_alcohol": min_a, "max_alcohol": max_a,
                    "max_sugar": max_z, "min_acidity": min_ac, "max_price": max_p,
                })
            except ApiError as e:
                stile.errore(e)
                return
            st.session_state[PROFILO_ATTIVO] = nuovo["id"]
            st.rerun()


def _referenze(profilo: dict) -> None:
    try:
        vini = api.vini_per_profilo(profilo["id"])
    except ApiError as e:
        stile.errore(e)
        return
    if not vini:
        st.info("Nessuna referenza risponde a questo profilo. I criteri sono troppo stretti: "
                "prova ad allargare un intervallo.")
        return

    st.caption(f"{len(vini)} referenze, ordinate per margine in euro")
    tabella = pd.DataFrame([{
        "id": v["id"], "Referenza": titolo_vino(v["name"]), "Lotto": lotto_vino(v["name"]),
        "Qualità": v["quality"], "Alcol": v["alcohol"], "Prezzo": v["price_eur"],
        "Margine %": v["margin_pct"], "Margine €": v["margine_euro"],
    } for v in vini])
    versione = st.session_state.get("vend_versione", 0)
    evento = st.dataframe(
        tabella, hide_index=True, width="stretch",
        on_select="rerun", selection_mode="single-row", key=f"vend_tabella_{versione}",
        column_order=[c for c in tabella.columns if c != "id"],
        column_config={
            "Qualità": st.column_config.NumberColumn(format="%d/10"),
            "Alcol": st.column_config.NumberColumn(format="%.1f%%"),
            "Prezzo": st.column_config.NumberColumn(format="%.2f €"),
            "Margine %": st.column_config.NumberColumn(format="%.1f%%"),
            "Margine €": st.column_config.NumberColumn(format="%.2f €"),
        },
    )
    if evento.selection.rows:
        st.session_state["vend_versione"] = versione + 1
        routing.apri_vino(int(tabella.iloc[evento.selection.rows[0]]["id"]))

    stile.nota(
        "<strong>Le due colonne di margine dicono cose diverse.</strong> La percentuale premia le "
        "referenze economiche ad alta rotazione, il valore in euro quelle di fascia alta. "
        "L'ordinamento qui è sul margine in euro, cioè su quanto entra in cassa per bottiglia. "
        "Prezzo e margine sono <em>simulati</em> con una logica di business dichiarata, non "
        "sono listini reali."
    )


def pagina() -> None:
    st.title("Vendite")
    cruscotto, profili_tab = st.tabs(["Cruscotto", "Profili di mercato"])
    with cruscotto:
        _cruscotto()
    with profili_tab:
        _profili()


def _profili() -> None:
    st.markdown("Descrivi cosa cerca un canale e trova le referenze che vi rispondono, "
                "ordinate per margine.")

    try:
        profili = api.profili()
    except ApiError as e:
        stile.errore(e)
        return

    _nuovo_profilo()

    if not profili:
        st.info("Nessun profilo ancora. Creane uno descrivendo cosa cerca il canale.")
        return

    per_id = {p["id"]: p for p in profili}
    attivo = st.session_state.get(PROFILO_ATTIVO)
    indice = list(per_id).index(attivo) if attivo in per_id else 0
    scelto = st.radio("Profilo", list(per_id), index=indice, horizontal=True,
                      format_func=lambda i: per_id[i]["name"])
    st.session_state[PROFILO_ATTIVO] = scelto
    profilo = per_id[scelto]

    with st.container(border=True):
        c1, c2 = st.columns([5, 1])
        c1.markdown(f"**{profilo['name']}**")
        if profilo.get("notes"):
            c1.caption(profilo["notes"])
        c1.markdown(descrivi_criteri(profilo))
        conferma = c2.checkbox("Confermo", key=f"conferma_{scelto}")
        if c2.button("Elimina", disabled=not conferma, key=f"elimina_{scelto}"):
            try:
                api.elimina_profilo(scelto)
            except ApiError as e:
                stile.errore(e)
                return
            st.session_state.pop(PROFILO_ATTIVO, None)
            st.rerun()

    _referenze(profilo)
