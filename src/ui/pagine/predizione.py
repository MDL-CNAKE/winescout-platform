"""Predizione su un lotto NON ancora a catalogo.

Il caso d'uso e' l'enologo con un'analisi in mano e una vasca in
lavorazione: il vino non e' in catalogo perche' non e' ancora imbottigliato.
Per un vino gia' in catalogo la scheda ha i valori precompilati.
"""
import streamlit as st

from src.ui import api, routing, stile
from src.ui.api import ApiError

# (campo, etichetta, valore iniziale, minimo, massimo, passo)
CAMPI = [
    ("fixed_acidity", "Acidità fissa (g/L)", 7.0, 4.0, 16.0, 0.1),
    ("volatile_acidity", "Acidità volatile (g/L)", 0.5, 0.1, 1.6, 0.01),
    ("citric_acid", "Acido citrico (g/L)", 0.3, 0.0, 1.0, 0.01),
    ("residual_sugar", "Zucchero residuo (g/L)", 2.0, 0.5, 65.0, 0.1),
    ("chlorides", "Cloruri (g/L)", 0.08, 0.01, 0.6, 0.001),
    ("free_sulfur_dioxide", "SO₂ libera (mg/L)", 15.0, 1.0, 289.0, 1.0),
    ("total_sulfur_dioxide", "SO₂ totale (mg/L)", 100.0, 6.0, 440.0, 1.0),
    ("density", "Densità (g/cm³)", 0.997, 0.98, 1.04, 0.0001),
    ("ph", "pH", 3.3, 2.7, 4.0, 0.01),
    ("sulphates", "Solfati (g/L)", 0.6, 0.3, 2.0, 0.01),
    ("alcohol", "Alcol (% vol)", 10.0, 8.0, 15.0, 0.1),
]


def pagina() -> None:
    st.title("Predizione della qualità")
    st.markdown(
        "Per un lotto **non ancora a catalogo**: inserisci i valori dell'analisi e ottieni "
        "la stima del punteggio (0-10). Per un vino già in catalogo apri la sua scheda, "
        "dove i valori sono già compilati."
    )

    with st.form("predizione"):
        tipo = st.segmented_control("Tipo di vino", ["red", "white"], default="red",
                                    format_func={"red": "Rosso", "white": "Bianco"}.get)
        colonne = st.columns(3)
        valori = {}
        for i, (campo, etichetta, iniziale, minimo, massimo, passo) in enumerate(CAMPI):
            formato = "%.4f" if passo < 0.001 else ("%.3f" if passo < 0.01 else "%.2f")
            valori[campo] = colonne[i % 3].number_input(
                etichetta, min_value=minimo, max_value=massimo, value=iniziale,
                step=passo, format=formato)
        invia = st.form_submit_button("Predici qualità", type="primary")

    if invia:
        try:
            st.session_state["pred_nuovo"] = api.predici({"type": tipo or "red", **valori})
        except ApiError as e:
            stile.errore(e)

    esito = st.session_state.get("pred_nuovo")
    if esito is not None:
        c1, c2 = st.columns([1, 3])
        c1.metric("Punteggio stimato", f"{esito:.1f}/10", border=True)
        c2.caption(
            "Il punteggio reale può variare per fattori non chimici (annata, terroir, "
            "affinamento) che il dataset non contiene."
        )

    stile.nota(stile.NOTA_PREDIZIONE)
    if "modello" in routing.PAGINE:
        st.page_link(routing.PAGINE["modello"], label="Cosa guida la previsione e come è stata misurata",
                     icon=":material/insights:")
