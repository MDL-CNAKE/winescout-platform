"""WineScout - Trasformare l'istinto del sommelier in algoritmi predittivi."""
import os
import joblib
import pandas as pd
import requests
import streamlit as st
import mysql.connector
from dotenv import load_dotenv
from models.recommender import WineRecommender, FEATURES

load_dotenv()
DB = dict(host=os.getenv("DB_HOST", "127.0.0.1"), port=3306, user="winescout",
          password="winescout", database="winescout")
MODEL_PATH = "models/quality_model.pkl"

st.set_page_config(page_title="WineScout", page_icon="🍷", layout="wide")


@st.cache_data
def load_wines() -> pd.DataFrame:
    conn = mysql.connector.connect(**DB)
    cur = conn.cursor()
    cur.execute("SELECT id, type, " + ", ".join(FEATURES) + ", quality FROM wines")
    df = pd.DataFrame(cur.fetchall(), columns=[c[0] for c in cur.description])
    conn.close()
    df[FEATURES] = df[FEATURES].astype(float)
    return df


@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


@st.cache_resource
def load_recommender() -> WineRecommender:
    return WineRecommender()


def sommelier_note(wine: pd.Series) -> str:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        return ("⚠️ Nessuna chiave API configurata. Crea un file .env con "
                "OPENROUTER_API_KEY=... per attivare il Sommelier Virtuale.")
    system = (
        "Sei un sommelier professionista AIS. Scrivi una nota di degustazione "
        "plausibile in italiano, strutturata in: esame visivo, olfattivo, "
        "gustativo, persistenza e un abbinamento cibo-vino. Basati SOLO sui "
        "parametri chimici forniti. Massimo 150 parole. Concludi ricordando "
        "che la nota e' generata da AI a partire da dati chimici."
    )
    user = (f"Vino {wine['type']}: alcol {wine['alcohol']}%, pH {wine['ph']}, "
            f"acidita' volatile {wine['volatile_acidity']} g/L, zucchero residuo "
            f"{wine['residual_sugar']} g/L, solfati {wine['sulphates']} g/L, "
            f"qualita' valutata {wine['quality']}/10.")
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": os.getenv("LLM_MODEL", "meta-llama/llama-3.1-8b-instruct"),
              "messages": [{"role": "system", "content": system},
                           {"role": "user", "content": user}]},
        timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


st.title("🍷 WineScout")
st.caption("Trasformare l'istinto del sommelier in algoritmi predittivi")
page = st.sidebar.radio("Sezione", ["Catalogo", "Predici qualita'",
                                    "Raccomandazioni", "Sommelier virtuale"])
st.sidebar.info("Questa app usa Machine Learning e AI generativa. Le predizioni "
                "sono un supporto decisionale, non sostituiscono il giudizio "
                "di un esperto. Dataset: vini portoghesi UCI (solo rossi/bianchi).")

try:
    wines = load_wines()
except Exception as e:
    st.error(f"Database non raggiungibile: {e}. Avvia con: docker compose up -d mysql")
    st.stop()

if page == "Catalogo":
    c1, c2 = st.columns(2)
    tipo = c1.multiselect("Tipo", ["red", "white"], default=["red", "white"])
    qmin, qmax = c2.slider("Qualita'", 3, 9, (3, 9))
    view = wines[wines["type"].isin(tipo) & wines["quality"].between(qmin, qmax)]
    st.metric("Vini trovati", len(view))
    st.dataframe(view, use_container_width=True, height=450)

elif page == "Predici qualita'":
    st.subheader("Stima la qualita' di un vino dalle sue analisi chimiche")
    tipo = st.selectbox("Tipo", ["red", "white"])
    cols = st.columns(4)
    values = {}
    for i, feat in enumerate(FEATURES):
        default = float(wines[wines["type"] == tipo][feat].median())
        values[feat] = cols[i % 4].number_input(feat.replace("_", " "), value=default)
    if st.button("Predici", type="primary"):
        X = pd.DataFrame([{"type": tipo, **values}])
        pred = load_model().predict(X)[0]
        st.success(f"Qualita' stimata: **{pred:.2f} / 10**")
        st.caption("Modello: Random Forest (RMSE 0.57 su test set). "
                   "La predizione e' indicativa.")

elif page == "Raccomandazioni":
    st.subheader("Trova i 'cugini chimici' di un vino")
    wine_id = st.selectbox("Vino di partenza (id)", wines["id"])
    top_n = st.slider("Quante raccomandazioni", 3, 10, 5)
    base = wines[wines["id"] == wine_id].iloc[0]
    st.write(f"Partenza: **{base['type']}**, alcol {base['alcohol']}%, "
             f"qualita' {base['quality']}/10")
    st.dataframe(load_recommender().recommend(int(wine_id), top_n),
                 use_container_width=True)

else:
    st.subheader("🤖 Sommelier Virtuale (AI generativa)")
    st.warning("Le note sono generate da un'intelligenza artificiale a partire "
               "dai soli dati chimici: non derivano da una degustazione reale.")
    wine_id = st.selectbox("Scegli un vino", wines["id"])
    if st.button("Genera nota di degustazione", type="primary"):
        with st.spinner("Il sommelier sta degustando..."):
            st.markdown(sommelier_note(wines[wines["id"] == wine_id].iloc[0]))
