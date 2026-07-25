"""WineScout Platform - Applicazione Streamlit.

Interfaccia utente che integra tutte le componenti del progetto: catalogo
vini persistito su MySQL, modello di predizione qualita (scikit-learn +
joblib), motore di raccomandazione content-based (similarita coseno) e
sommelier virtuale basato su LLM (con modalita demo se manca la API key).
"""
import sys
import os
import joblib
import pandas as pd
import requests
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.connection import DatabaseConnection
from src.models.recommender import WineRecommender

st.set_page_config(page_title="WineScout Platform", page_icon="🍷", layout="wide")


@st.cache_resource
def load_model():
    """Carica il modello di predizione qualita gia addestrato (joblib)."""
    return joblib.load("models/quality_model.pkl")


@st.cache_resource
def get_recommender() -> WineRecommender:
    """Costruisce il motore di raccomandazione una sola volta e lo mantiene
    in cache: ricalcolare la matrice di similarita a ogni click sarebbe
    inutilmente costoso (6497x6497 valori)."""
    return WineRecommender()


@st.cache_data
def get_wines_from_db() -> pd.DataFrame:
    """Carica il catalogo vini, incluse le colonne di business (prezzo,
    margine) aggiunte con la migrazione V3."""
    with DatabaseConnection() as conn:
        return pd.read_sql(
            "SELECT id, name, type, alcohol, ph, residual_sugar, quality, "
            "price_eur, margin_pct FROM wines",
            conn,
        )


st.title("🍷 WineScout Platform")
st.markdown("*Trasformare l'istinto del sommelier in algoritmi predittivi grazie al Machine Learning*")
st.markdown("---")

st.sidebar.header("Navigazione")
page = st.sidebar.radio("Scegli una sezione:", [
    "🍷 Catalogo Vini",
    "🔮 Predizione Qualità",
    "🎯 Raccomandazioni",
    "🤖 Sommelier Virtuale",
])

# ==========================================
# PAGINA 1: CATALOGO VINI
# ==========================================
if page == "🍷 Catalogo Vini":
    st.header("Catalogo Vini (Anteprima)")
    st.info("Dati caricati direttamente dal database MySQL persistente.")

    df = get_wines_from_db()

    col1, col2, col3 = st.columns(3)
    with col1:
        type_filter = st.selectbox("Filtra per Tipo", ["Tutti", "red", "white"])
    with col2:
        quality_filter = st.slider(
            "Filtra per Qualità Minima",
            int(df["quality"].min()), int(df["quality"].max()), int(df["quality"].min()),
        )
    with col3:
        price_max = st.slider(
            "Prezzo Massimo (EUR)",
            float(df["price_eur"].min()), float(df["price_eur"].max()), float(df["price_eur"].max()),
        )

    filtered_df = df.copy()
    if type_filter != "Tutti":
        filtered_df = filtered_df[filtered_df["type"] == type_filter]
    filtered_df = filtered_df[filtered_df["quality"] >= quality_filter]
    filtered_df = filtered_df[filtered_df["price_eur"] <= price_max]

    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    # Nota etica: il prezzo e il margine sono dati simulati (il dataset UCI
    # di origine non contiene informazioni commerciali), va dichiarato
    # esplicitamente all'utente per trasparenza.
    st.caption(
        "Nota: prezzo e margine sono valori simulati con una logica di "
        "business (vedi src/pricing.py), non prezzi reali di listino."
    )

    if len(filtered_df) > 0:
        c1, c2, c3 = st.columns(3)
        c1.metric("Vini nel filtro", len(filtered_df))
        c2.metric("Prezzo medio", f"{filtered_df['price_eur'].mean():.2f} EUR")
        c3.metric("Margine medio", f"{filtered_df['margin_pct'].mean():.1f} %")

# ==========================================
# PAGINA 2: PREDIZIONE QUALITÀ
# ==========================================
elif page == "🔮 Predizione Qualità":
    st.header("Predizione Punteggio Qualità")
    st.markdown("Inserisci le caratteristiche chimiche del vino per ottenere una stima del punteggio (0-10).")

    model = load_model()

    col1, col2 = st.columns(2)
    with col1:
        w_type = st.selectbox("Tipo", ["red", "white"])
        fixed_acidity = st.slider("Acidità Fissa", 4.0, 16.0, 7.0)
        volatile_acidity = st.slider("Acidità Volatile", 0.1, 1.6, 0.5)
        citric_acid = st.slider("Acido Citrico", 0.0, 1.0, 0.3)
        residual_sugar = st.slider("Zucchero Residuo", 0.5, 65.0, 2.0)
        chlorides = st.slider("Cloruri", 0.01, 0.6, 0.08)
    with col2:
        free_sulfur_dioxide = st.slider("SO2 Libera", 1.0, 289.0, 15.0)
        total_sulfur_dioxide = st.slider("SO2 Totale", 6.0, 440.0, 100.0)
        density = st.slider("Densità", 0.98, 1.04, 0.997)
        ph = st.slider("pH", 2.7, 4.0, 3.3)
        sulphates = st.slider("Solfati", 0.3, 2.0, 0.6)
        alcohol = st.slider("Alcol (%)", 8.0, 15.0, 10.0)

    if st.button("🔮 Predici Qualità", type="primary"):
        input_data = pd.DataFrame([{
            "type": w_type,
            "fixed_acidity": fixed_acidity,
            "volatile_acidity": volatile_acidity,
            "citric_acid": citric_acid,
            "residual_sugar": residual_sugar,
            "chlorides": chlorides,
            "free_sulfur_dioxide": free_sulfur_dioxide,
            "total_sulfur_dioxide": total_sulfur_dioxide,
            "density": density,
            "ph": ph,
            "sulphates": sulphates,
            "alcohol": alcohol,
        }])
        # Ordine esplicito delle colonne: la Pipeline seleziona per nome, ma
        # tenere l'ordine coerente con il training evita ambiguita.
        feature_order = ["type", "fixed_acidity", "volatile_acidity", "citric_acid", "residual_sugar",
                          "chlorides", "free_sulfur_dioxide", "total_sulfur_dioxide", "density", "ph",
                          "sulphates", "alcohol"]
        prediction = model.predict(input_data[feature_order])[0]
        st.success(f"### Punteggio Qualità Stimato: {prediction:.1f} / 10")
        st.caption("Nota: questo e' un modello predittivo basato su dati storici. Il punteggio reale puo variare.")

# ==========================================
# PAGINA 3: RACCOMANDAZIONI
# ==========================================
elif page == "🎯 Raccomandazioni":
    st.header("Motore di Raccomandazione Content-Based")
    st.markdown("Trova vini chimicamente simili utilizzando la **Similarità Coseno**.")

    recommender = get_recommender()
    wine_ids = recommender.df["id"].tolist()
    selected_id = st.selectbox("Seleziona un vino di partenza (ID):", wine_ids)

    col_a, col_b = st.columns(2)
    find_similar = col_a.button("🎯 Trova Vini Simili", type="primary")
    find_cheaper = col_b.button("💶 Trova Alternativa Più Economica")

    if find_similar:
        try:
            recommendations = recommender.recommend(wine_id=selected_id, top_n=5, same_type=True)
            st.subheader(f"Top 5 vini simili al vino ID {selected_id}")
            display_df = recommendations[["id", "name", "type", "alcohol", "ph", "quality", "price_eur", "similarity"]].copy()
            display_df["similarity"] = display_df["similarity"].apply(lambda x: f"{x:.2%}")
            display_df = display_df.rename(columns={
                "id": "ID Vino", "name": "Nome", "type": "Tipo", "alcohol": "Alcol (%)",
                "ph": "pH", "quality": "Qualità", "price_eur": "Prezzo (EUR)", "similarity": "Similarità",
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        except ValueError as e:
            st.error(str(e))

    if find_cheaper:
        try:
            alternatives = recommender.find_cheaper_alternative(wine_id=selected_id)
            if alternatives.empty:
                st.warning("Nessuna alternativa più economica trovata tra i vini chimicamente simili.")
            else:
                base_price = float(recommender.df.loc[recommender.df["id"] == selected_id, "price_eur"].iloc[0])
                st.subheader(f"Alternative più economiche al vino ID {selected_id} ({base_price:.2f} EUR)")
                display_df = alternatives[["id", "name", "price_eur", "similarity", "savings_pct"]].copy()
                display_df["similarity"] = display_df["similarity"].apply(lambda x: f"{x:.2%}")
                display_df["savings_pct"] = display_df["savings_pct"].apply(lambda x: f"{x:.1%}")
                display_df = display_df.rename(columns={
                    "id": "ID Vino", "name": "Nome", "price_eur": "Prezzo (EUR)",
                    "similarity": "Similarità", "savings_pct": "Risparmio",
                })
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                st.caption(
                    "Ordinato per un punteggio combinato: 70% similarità chimica, "
                    "30% risparmio economico — privilegia la coerenza del profilo "
                    "gustativo rispetto al solo prezzo più basso."
                )
        except ValueError as e:
            st.error(str(e))

# ==========================================
# PAGINA 4: SOMMELIER VIRTUALE (LLM)
# ==========================================
elif page == "🤖 Sommelier Virtuale":
    st.header("Sommelier Virtuale AI")
    st.markdown("Chiedi consigli su abbinamenti, note di degustazione o curiosità sul vino.")

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model_name = os.getenv("LLM_MODEL", "meta-llama/llama-3.1-8b-instruct")

    prompt = st.text_area(
        "La tua domanda per il Sommelier:",
        placeholder="Es: 'Qual è l'abbinamento ideale per un Pinot Nero con 13% di alcol e note di frutta rossa?'",
        height=100,
    )

    if st.button("🤖 Chiedi al Sommelier", type="primary"):
        if not api_key or api_key == "metti_qui_la_tua_chiave":
            # Modalita demo: l'app resta dimostrabile anche senza una chiave
            # API valida, requisito implicito per una demo affidabile.
            st.warning("⚠️ **Modalità Demo:** API Key non configurata. Ecco una risposta simulata.")
            st.info(
                "**Sommelier AI:** Basandomi sulle migliori pratiche, un vino con queste "
                "caratteristiche si abbina splendidamente a carni rosse arrosto o funghi "
                "porcini. *(Risposta di fallback. Configura OPENROUTER_API_KEY nel file "
                ".env per risposte reali).*"
            )
        else:
            with st.spinner("Il sommelier sta preparando la risposta..."):
                try:
                    response = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": model_name,
                            "messages": [
                                {"role": "system", "content": (
                                    "Sei un sommelier esperto e professionale. Rispondi in "
                                    "italiano in modo elegante, citando esame visivo, "
                                    "olfattivo e gustativo quando pertinente."
                                )},
                                {"role": "user", "content": prompt},
                            ],
                        },
                    )
                    response.raise_for_status()
                    answer = response.json()["choices"][0]["message"]["content"]
                    st.markdown(f"**Risposta del Sommelier:**\n\n{answer}")
                except Exception as e:
                    st.error(f"Errore nella chiamata API: {e}")
