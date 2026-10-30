"""Il modello: quanto e' affidabile e come e' stato misurato.

I numeri delle tabelle sono quelli documentati in docs/model_limitations.md
e riproducibili con gli script indicati accanto. Non vengono ricalcolati
qui: alcuni esperimenti richiedono minuti di cross-validation, e l'interfaccia
non e' il posto per rieseguirli. L'importanza delle variabili invece e'
calcolata dal backend sul modello in uso.
"""
import pandas as pd
import streamlit as st

from src.ui import api, stile
from src.ui.api import ApiError


def _metriche_oneste() -> None:
    c = st.columns(4)
    c[0].metric("R² cross-validation raggruppata", "0,385", border=True)
    c[1].metric("R² test senza righe ripetute", "0,397", border=True)
    c[2].metric("RMSE sul test", "0,68", border=True)
    c[3].metric("Righe duplicate nel dataset", "1.177 / 6.497", border=True)
    st.caption(
        "Il modello spiega circa il 40% della variabilità. Il 77% dei vini sta in due sole "
        "classi (5 e 6): su un target così compresso, con le sole variabili chimiche, il "
        "valore è coerente con la letteratura su questo dataset."
    )


def _leakage() -> None:
    st.subheader("Il 29% dell'R² era memoria, non predizione")
    st.markdown(
        "Il dataset contiene 1.177 righe identiche su 6.497. Con uno split casuale una "
        "copia va in addestramento e l'altra in test: il modello viene premiato per averla "
        "memorizzata. Per isolare la causa servono tre scenari, non due."
    )
    st.dataframe(pd.DataFrame([
        {"Scenario": "A. Split casuale (com'era)", "Cosa cambia": "—",
         "RMSE": 0.569, "MAE": 0.403, "R²": 0.561},
        {"Scenario": "C. Raggruppato per firma chimica", "Cosa cambia": "solo la fuga",
         "RMSE": 0.679, "MAE": 0.528, "R²": 0.398},
        {"Scenario": "B. Deduplicato", "Cosa cambia": "fuga e dimensione del dataset",
         "RMSE": 0.675, "MAE": 0.515, "R²": 0.373},
    ]), hide_index=True, width="stretch")
    st.markdown(
        "Il confronto onesto è **A contro C**: stessi dati, l'unica differenza è la fuga. "
        "B cambia due cose insieme e da solo non direbbe quale ha prodotto il calo."
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**La cross-validation non protegge**")
        st.dataframe(pd.DataFrame([
            {"Cross-validation 5-fold": "KFold con shuffle", "R²": 0.521},
            {"Cross-validation 5-fold": "GroupKFold sulla firma chimica", "R²": 0.385},
        ]), hide_index=True, width="stretch")
        st.caption("Mescolare i fold sparge le copie esattamente come lo split. Serve raggruppare.")
    with c2:
        st.markdown("**La fuga non è neutra fra gli algoritmi**")
        st.dataframe(pd.DataFrame([
            {"Modello": "RandomForest", "R² contaminato": 0.521, "R² raggruppato": 0.385, "Guadagno": 0.136},
            {"Modello": "GradientBoosting", "R² contaminato": 0.390, "R² raggruppato": 0.364, "Guadagno": 0.026},
            {"Modello": "LinearRegression", "R² contaminato": 0.292, "R² raggruppato": 0.289, "Guadagno": 0.003},
        ]), hide_index=True, width="stretch")
        st.caption(
            "Una retta non può memorizzare una riga, 200 alberi sì. Il vantaggio della "
            "RandomForest sul GradientBoosting passa da 0,131 a 0,021: la scelta regge, ma "
            "di poco."
        )
    st.caption("Fonti: src/models/leakage_experiment.py, src/models/compare_models.py, "
               "docs/model_limitations.md")


def _importanza() -> None:
    st.subheader("Cosa guida la qualità")
    st.markdown(
        "Quanto peggiora la previsione se si rende inutilizzabile una variabile alla volta. "
        "Se rompere un parametro non peggiora nulla, quel parametro non serviva."
    )
    try:
        with st.spinner("Analisi delle variabili in corso (la prima volta richiede qualche secondo)..."):
            dati = api.importanza()
    except ApiError as e:
        stile.errore(e)
        return

    tabella = pd.DataFrame([{
        "Variabile": v["etichetta"],
        "Quota": v["quota"],
        "Calo di R²": v["importanza"],
        "± incertezza": v["incertezza"],
        "Significato": v["significato"],
    } for v in dati])
    st.dataframe(
        tabella, hide_index=True, width="stretch",
        column_config={
            "Quota": st.column_config.ProgressColumn(
                format="%.1f%%", min_value=0, max_value=float(tabella["Quota"].max() or 1)),
            "Calo di R²": st.column_config.NumberColumn(format="%.3f"),
            "± incertezza": st.column_config.NumberColumn(format="%.3f"),
            "Significato": st.column_config.TextColumn(width="large"),
        },
    )
    stile.nota(
        "<strong>Come è calcolata.</strong> Importanza per permutazione: si mescolano a caso i "
        "valori di una variabile e si misura il calo di R². Non si usa l'importanza interna "
        "del RandomForest perché sovrastima le variabili con molti valori distinti. Il "
        "calcolo avviene sul test set raggruppato, cioè su dati mai visti: dice cosa il "
        "modello <em>generalizza</em>, non cosa ha memorizzato. L'incertezza sta accanto alla "
        "media perché la permutazione è casuale. È una correlazione, non una causa."
    )


def _rag() -> None:
    st.subheader("Il retrieval di SVEVA, misurato")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Tre strategie sulle stesse 12 domande (top_k 3)**")
        st.dataframe(pd.DataFrame([
            {"Strategia": "Ibrida (in uso)", "Hit rate": "75%", "MRR": 0.653},
            {"Strategia": "Solo lessicale", "Hit rate": "58%", "MRR": 0.542},
            {"Strategia": "Solo semantica", "Hit rate": "42%", "MRR": 0.361},
        ]), hide_index=True, width="stretch")
        st.caption("La semantica pura fallisce su 'ndole' e 'piatto africano': il modello di "
                   "embedding rappresenta male i piatti extra-europei.")
    with c2:
        st.markdown("**Insieme di verifica tenuto da parte (top_k 5)**")
        st.dataframe(pd.DataFrame([
            {"Insieme": "Sviluppo", "Domande": 36, "Hit rate": "89%", "MRR": 0.485},
            {"Insieme": "Verifica", "Domande": 11, "Hit rate": "91%", "MRR": 0.571},
        ]), hide_index=True, width="stretch")
        st.caption("La ground truth generata dall'LLM sbagliava nel 13% dei casi ed è stata "
                   "corretta a mano (src/rag/revisione_manuale.py).")


def pagina() -> None:
    st.title("Il modello, misurato")
    st.markdown(
        "Quanto fidarsi delle stime, e come sono stati trovati i problemi che gonfiavano i "
        "numeri dichiarati per gran parte dello sviluppo."
    )
    _metriche_oneste()
    st.divider()
    _leakage()
    st.divider()
    _importanza()
    st.divider()
    _rag()
