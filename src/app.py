"""
WineScout Platform - Applicazione Streamlit
Trasformare l'istinto del sommelier in algoritmi predittivi grazie al Machine Learning
"""
import sys
import os
import joblib
import pandas as pd
import requests
import streamlit as st

# Aggiungi la root del progetto al path per importare i moduli
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.connection import DatabaseConnection
from src.models.recommender import WineRecommender

# Configurazione pagina
st.set_page_config(page_title="WineScout Platform", page_icon="🍷", layout="wide")

# Cache per evitare di ricaricare modello e DB a ogni interazione
@st.cache_resource
def load_model():
    return joblib.load("models/quality_model.pkl")

@st.cache_data
def get_wines_from_db():
    with DatabaseConnection() as conn:
        return pd.read_sql("SELECT id, type, alcohol, ph, residual_sugar, quality FROM wines LIMIT 200", conn)

st.title("🍷 WineScout Platform")
st.markdown("*Trasformare l'istinto del sommelier in algoritmi predittivi grazie al Machine Learning*")
st.markdown("---")

# Sidebar per la navigazione
st.sidebar.header("Navigazione")
page = st.sidebar.radio("Scegli una sezione:", [
    "🍷 Catalogo Vini", 
    "🔮 Predizione Qualità", 
    "🎯 Raccomandazioni", 
    "🤖 Sommelier Virtuale"
])

# ==========================================
# PAGINA 1: CATALOGO VINI
# ==========================================
if page == "🍷 Catalogo Vini":
    st.header("Catalogo Vini (Anteprima)")
    st.info("Dati caricati direttamente dal database MySQL persistente.")
    
    df = get_wines_from_db()
    
    # Filtri
    col1, col2 = st.columns(2)
    with col1:
        type_filter = st.selectbox("Filtra per Tipo", ["Tutti", "red", "white"])
    with col2:
        quality_filter = st.slider("Filtra per Qualità Minima", int(df['quality'].min()), int(df['quality'].max()), int(df['quality'].min()))
    
    # Applica filtri
    filtered_df = df.copy()
    if type_filter != "Tutti":
        filtered_df = filtered_df[filtered_df['type'] == type_filter]
    filtered_df = filtered_df[filtered_df['quality'] >= quality_filter]
    
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

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
        # Crea il DataFrame per la predizione (stesso ordine delle feature usate nel training)
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
            "alcohol": alcohol
        }])
        
        # Il modello si aspetta le colonne nello stesso ordine del training
        feature_order = ["type", "fixed_acidity", "volatile_acidity", "citric_acid", "residual_sugar",
                         "chlorides", "free_sulfur_dioxide", "total_sulfur_dioxide", "density", "ph", "sulphates", "alcohol"]
        
        prediction = model.predict(input_data[feature_order])[0]
        
        st.success(f"### Punteggio Qualità Stimato: {prediction:.1f} / 10")
        st.caption("Nota: Questo è un modello predittivo basato su dati storici. Il punteggio reale può variare.")

# ==========================================
# PAGINA 3: RACCOMANDAZIONI
# ==========================================
elif page == "🎯 Raccomandazioni":
    st.header("Motore di Raccomandazione Content-Based")
    st.markdown("Trova vini chimicamente simili utilizzando la **Similarità Coseno**.")
    
    with st.spinner("Caricamento motore di raccomandazione..."):
        recommender = WineRecommender()
    
    # Prendi una lista di ID per il dropdown
    wine_ids = recommender.df["id"].tolist()
    selected_id = st.selectbox("Seleziona un vino di partenza (ID):", wine_ids)
    
    if st.button("🎯 Trova Vini Simili", type="primary"):
        try:
            recommendations = recommender.recommend(wine_id=selected_id, top_n=5, same_type=True)
            
            st.subheader(f"Top 5 vini simili al vino ID {selected_id}")
            
            # Formatta la tabella per la visualizzazione
            display_df = recommendations[["id", "type", "alcohol", "ph", "quality", "similarity"]].copy()
            display_df["similarity"] = display_df["similarity"].apply(lambda x: f"{x:.2%}")
            display_df = display_df.rename(columns={
                "id": "ID Vino", "type": "Tipo", "alcohol": "Alcol (%)", 
                "ph": "pH", "quality": "Qualità", "similarity": "Similarità"
            })
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
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
    
    prompt = st.text_area("La tua domanda per il Sommelier:", 
                          placeholder="Es: 'Qual è l'abbinamento ideale per un Pinot Nero con 13% di alcol e note di frutta rossa?'",
                          height=100)
    
    if st.button("🤖 Chiedi al Sommelier", type="primary"):
        if not api_key or api_key == "metti_qui_la_tua_chiave":
            st.warning("⚠️ **Modalità Demo:** API Key non configurata. Ecco una risposta simulata per mostrarti il funzionamento dell'interfaccia.")
            st.info(f"**Sommelier AI:** Basandomi sulle migliori pratiche, un vino con queste caratteristiche si abbina splendidamente a carni rosse arrosto o funghi porcini. La sua struttura richiede un piatto con buona persistenza gustativa. *(Questa è una risposta di fallback. Configura OPENROUTER_API_KEY nel file .env per risposte reali).*")
        else:
            with st.spinner("Il sommelier sta preparando la risposta..."):
                try:
                    response = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model_name,
                            "messages": [
                                {"role": "system", "content": "Sei un sommelier esperto e professionale. Rispondi in italiano in modo elegante, citando esame visivo, olfattivo e gustativo quando pertinente."},
                                {"role": "user", "content": prompt}
                            ]
                        }
                    )
                    response.raise_for_status()
                    result = response.json()
                    answer = result["choices"][0]["message"]["content"]
                    st.markdown(f"**Risposta del Sommelier:**\n\n{answer}")
                except Exception as e:
                    st.error(f"Errore nella chiamata API: {e}")
