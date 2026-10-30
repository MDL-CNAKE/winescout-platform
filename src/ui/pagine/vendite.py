"""Vendite: profili di mercato e redditivita' delle referenze.

I profili li scrive chi vende: il dataset non contiene geografia, clienti ne'
storico vendite, quindi nulla permette di dedurre cosa piaccia a un mercato.
La conoscenza commerciale resta umana e viene dichiarata; il sistema cerca
fra 6.497 lotti quelli che vi rispondono.
"""
import pandas as pd
import streamlit as st

from src.ui import api, routing, stile
from src.ui.api import ApiError
from src.ui.formato import descrivi_criteri, lotto_vino, titolo_vino

PROFILO_ATTIVO = "vendite_profilo"


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
    st.title("Profili di mercato")
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
