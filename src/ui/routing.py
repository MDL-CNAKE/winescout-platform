"""Registro delle pagine e passaggio da una pagina all'altra.

Sta in un modulo a se' per evitare un import circolare: la navigazione
importa le pagine, e le pagine devono poter aprire la scheda di un vino.
Il registro viene riempito da src/ui/navigazione.py a ogni esecuzione e
contiene solo le pagine visibili al ruolo corrente: un collegamento verso una
pagina fuori dalla navigazione farebbe fallire Streamlit, quindi le pagine
controllano che la destinazione sia presente prima di mostrarlo.
"""
import streamlit as st

PAGINE: dict[str, st.Page] = {}

# Chiave di session_state del vino aperto nella scheda. Non e' la chiave di
# un widget: Streamlit cancella lo stato dei widget non mostrati, e il vino
# scelto deve sopravvivere al cambio di pagina.
VINO_SCELTO = "vino_scelto"
OPERATORE = "operatore_id"


def apri_vino(wine_id: int) -> None:
    """Apre la scheda del vino indicato."""
    st.session_state[VINO_SCELTO] = int(wine_id)
    st.switch_page(PAGINE["vino"])
