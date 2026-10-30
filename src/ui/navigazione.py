"""Navigazione per ruolo e scelta dell'operatore.

Stessa logica del frontend React (frontend/src/router.tsx): ogni ruolo vede
in navigazione gli strumenti del proprio mestiere. Non e' un sistema di
permessi — l'applicazione appartiene a una sola cantina e chiunque puo'
cambiare operatore — ma un modo di non mostrare tutto a tutti.
"""
import streamlit as st

from src.ui import api, routing, stile
from src.ui.api import ApiError
from src.ui.pagine import (catalogo, conservazione, in_arrivo, modello, packaging,
                           predizione, sveva, vendite, vino)

RUOLI = ("titolare", "enologo", "vendite", "logistica", "marketing")

# chiave: (titolo, icona, funzione). L'ordine e' quello della navigazione.
SEZIONI = {
    "catalogo": ("Catalogo", ":material/wine_bar:", catalogo.pagina),
    "vino": ("Scheda vino", ":material/description:", vino.pagina),
    "sveva": ("SVEVA", ":material/forum:", sveva.pagina),
    "predizione": ("Predizione", ":material/query_stats:", predizione.pagina),
    "modello": ("Il modello", ":material/insights:", modello.pagina),
    "conservazione": ("Conservazione", ":material/schedule:", conservazione.pagina),
    "vendite": ("Vendite", ":material/sell:", vendite.pagina),
    "packaging": ("Packaging", ":material/inventory_2:", packaging.pagina),
    "spedizioni": ("Spedizioni", ":material/local_shipping:", in_arrivo.spedizioni),
    "marketing": ("Marketing", ":material/campaign:", in_arrivo.marketing),
}

# La scheda vino e' visibile a tutti: ogni tabella apre la scheda di un lotto.
PER_RUOLO = {
    "titolare": list(SEZIONI),
    "enologo": ["catalogo", "vino", "sveva", "predizione", "modello", "conservazione"],
    "vendite": ["catalogo", "vino", "sveva", "vendite", "packaging", "marketing"],
    "logistica": ["catalogo", "vino", "packaging", "spedizioni"],
    "marketing": ["catalogo", "vino", "sveva", "vendite", "marketing"],
}


def pagine_per_ruolo(ruolo: str) -> list[st.Page]:
    """Crea le pagine del ruolo e le registra per i collegamenti interni."""
    routing.PAGINE.clear()
    visibili = PER_RUOLO.get(ruolo, PER_RUOLO["titolare"])
    for chiave in visibili:
        titolo, icona, funzione = SEZIONI[chiave]
        if chiave == "catalogo":
            # La pagina predefinita si apre all'indirizzo radice: non ha url_path.
            pagina = st.Page(funzione, title=titolo, icon=icona, default=True)
        else:
            # url_path esplicito: tutte le funzioni si chiamano "pagina" e
            # Streamlit non potrebbe ricavare indirizzi distinti dal nome.
            pagina = st.Page(funzione, title=titolo, icon=icona, url_path=chiave)
        routing.PAGINE[chiave] = pagina
    return list(routing.PAGINE.values())


def _form_nuovo_operatore() -> None:
    with st.expander("Aggiungi operatore"):
        with st.form("nuovo_operatore", clear_on_submit=True):
            nome = st.text_input("Nome", max_chars=60)
            ruolo = st.selectbox("Ruolo", RUOLI)
            if st.form_submit_button("Aggiungi"):
                if not nome.strip():
                    st.error("Il nome non può essere vuoto.")
                    return
                try:
                    nuovo = api.crea_operatore(nome.strip(), ruolo)
                except ApiError as e:
                    stile.errore(e)
                    return
                st.session_state[routing.OPERATORE] = nuovo["id"]
                st.rerun()


def scegli_operatore() -> str:
    """Selettore nella barra laterale. Restituisce il ruolo attivo."""
    try:
        operatori = api.operatori()
    except ApiError:
        operatori = []

    ruolo = "titolare"
    if operatori:
        per_id = {o["id"]: o for o in operatori}
        attuale = st.session_state.get(routing.OPERATORE)
        indice = list(per_id).index(attuale) if attuale in per_id else 0
        scelto = st.selectbox(
            "Chi sta lavorando", list(per_id), index=indice,
            format_func=lambda i: f"{per_id[i]['name']} · {per_id[i]['role']}",
        )
        st.session_state[routing.OPERATORE] = scelto
        ruolo = per_id[scelto]["role"]
    else:
        st.caption("Nessun operatore registrato: vista completa.")

    _form_nuovo_operatore()
    st.caption("Il ruolo sceglie le sezioni in navigazione. Non è un sistema di permessi.")
    return ruolo
