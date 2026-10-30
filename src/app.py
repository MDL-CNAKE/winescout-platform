"""CruScout — interfaccia Streamlit.

Avvio:  streamlit run src/app.py
Richiede il backend FastAPI attivo (BACKEND_URL, predefinito
http://localhost:8000): con Docker basta 'docker compose up'.

Questo file contiene solo l'impianto comune — marchio, scelta
dell'operatore, navigazione per ruolo. Le pagine sono in src/ui/pagine/, e
tutta la logica di dominio resta nel backend (vedi src/ui/api.py per il
perche').
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st  # noqa: E402

st.set_page_config(page_title="CruScout", page_icon=":material/wine_bar:", layout="wide")

from src.ui import api, navigazione, stile  # noqa: E402

stile.applica_stile()

with st.sidebar:
    stile.marchio()

if not api.backend_attivo():
    st.error(
        f"Il backend non risponde su {api.BACKEND_URL}. "
        "Avvialo con 'docker compose up backend' oppure, in locale, con "
        "'uvicorn backend.main:app --port 8000'."
    )
    st.stop()

with st.sidebar:
    ruolo = navigazione.scegli_operatore()

pagina = st.navigation(navigazione.pagine_per_ruolo(ruolo))

with st.sidebar:
    st.divider()
    st.caption("Dati: UCI Wine Quality (vini Vinho Verde). Prezzi e margini simulati.")

pagina.run()
