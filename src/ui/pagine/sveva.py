"""SVEVA — Sommelier Virtuale Esperta in Vini e Abbinamenti.

Due modalita', perche' sono due problemi diversi:

- CONOSCENZA (RAG): domande sul sapere enologico. La risposta si fonda sui
  passaggi recuperati dalla knowledge base. Ha memoria della conversazione.
- CATALOGO (function calling): domande sui dati della cantina. Il modello
  non li conosce: chiama strumenti tipizzati e il backend esegue le query.

La scelta e' dell'utente e non automatica: indovinare l'intento sbagliando
farebbe rispondere a memoria una domanda sui dati, cioe' esattamente il
fallimento che questa separazione evita.
"""
import json

import streamlit as st

from src.ui import api, stile
from src.ui.api import ApiError

STORICO = "sveva_storico"   # messaggi inviati al backend: {ruolo, contenuto}
DETTAGLI = "sveva_dettagli"  # per ogni risposta: fonti, metriche, memoria, demo
AGENTE = "sveva_agente"

AVATAR = {"user": ":material/person:", "assistant": ":material/wine_bar:"}


def _intestazione() -> None:
    c1, c2 = st.columns([1, 9])
    c1.markdown(stile.testa_sveva(72), unsafe_allow_html=True)
    with c2:
        st.title("SVEVA")
        st.caption("Sommelier Virtuale Esperta in Vini e Abbinamenti")
    st.markdown("Posso ragionare di abbinamenti, oppure andare a leggere cosa c'è davvero in catalogo.")


def _dettagli_risposta(d: dict) -> None:
    if d.get("demo_mode"):
        st.caption(":orange[Modalità demo: chiave LLM non configurata, risposta generata dalle regole.]")
    if d.get("sources"):
        with st.expander(f"Fonti consultate ({len(d['sources'])} passaggi)"):
            for passaggio in d["sources"]:
                righe = passaggio.splitlines()
                st.markdown(f"**{righe[0]}**")
                corpo = " ".join(righe[1:]).strip()
                st.caption(corpo[:400] + ("..." if len(corpo) > 400 else ""))
    # La finestra scorrevole e' invisibile: senza questo numero, quando SVEVA
    # "dimentica" sembra un difetto e non una politica di budget dichiarata.
    if d.get("messaggi_ricordati"):
        st.caption(f"Ha tenuto conto di {d['messaggi_ricordati']} messaggi precedenti.")
    stile.metriche(d.get("metriche"))


def _scegli_vino_contesto() -> int | None:
    if not st.toggle("Basa la risposta su un vino del catalogo", key="sveva_usa_vino"):
        return None
    try:
        sommario = api.vini_sommario()
    except ApiError as e:
        stile.errore(e)
        return None
    nomi = {w["id"]: w["name"] for w in sommario}
    return st.selectbox("Vino di riferimento", list(nomi), format_func=nomi.get, key="sveva_vino")


def _conoscenza() -> None:
    st.caption("Abbinamenti, note di degustazione, principi enologici. "
               "La risposta si basa sulla knowledge base.")
    st.session_state.setdefault(STORICO, [])
    st.session_state.setdefault(DETTAGLI, [])

    wine_id = _scegli_vino_contesto()

    for messaggio, dettaglio in zip(st.session_state[STORICO], st.session_state[DETTAGLI]):
        with st.chat_message(messaggio["ruolo"], avatar=AVATAR[messaggio["ruolo"]]):
            st.markdown(messaggio["contenuto"])
            if dettaglio:
                _dettagli_risposta(dettaglio)

    if st.session_state[STORICO] and st.button("Nuova conversazione"):
        st.session_state[STORICO] = []
        st.session_state[DETTAGLI] = []
        st.rerun()

    segnaposto = ("Continua pure: puoi dire 'e con il pesce?'" if st.session_state[STORICO]
                  else "Es: come abbino un piatto molto grasso?")
    domanda = st.chat_input(segnaposto)
    if not domanda:
        return

    with st.chat_message("user", avatar=AVATAR["user"]):
        st.markdown(domanda)
    with st.chat_message("assistant", avatar=AVATAR["assistant"]):
        with st.spinner("SVEVA sta pensando..."):
            try:
                # Lo storico parte PRIMA di aggiungere la domanda corrente: il
                # backend la riceve a parte e decide quanta memoria usare.
                r = api.chiedi_sommelier(domanda, wine_id, st.session_state[STORICO])
            except ApiError as e:
                stile.errore(e)
                return

    # Nuove liste invece di estendere quelle esistenti: lo storico appena
    # inviato resta com'era al momento della domanda.
    st.session_state[STORICO] = st.session_state[STORICO] + [
        {"ruolo": "user", "contenuto": domanda},
        {"ruolo": "assistant", "contenuto": r["answer"]},
    ]
    st.session_state[DETTAGLI] = st.session_state[DETTAGLI] + [None, {
        "demo_mode": r.get("demo_mode"),
        "sources": r.get("sources", []),
        "messaggi_ricordati": r.get("messaggi_ricordati", 0),
        "metriche": r.get("metriche"),
    }]
    st.rerun()


def _catalogo() -> None:
    st.caption("Quali lotti ho, a che prezzo, in che stato. SVEVA interroga il database: "
               "i numeri che cita vengono da lì.")
    with st.form("sveva_agente_form"):
        domanda = st.text_area("Domanda sul catalogo",
                               placeholder="Es: quali rossi ho sopra qualità 6 sotto i 15 euro?")
        invia = st.form_submit_button("Chiedi a SVEVA", type="primary")

    if invia and domanda.strip():
        with st.spinner("SVEVA sta interrogando il catalogo..."):
            try:
                st.session_state[AGENTE] = api.chiedi_agente(domanda)
            except ApiError as e:
                st.session_state.pop(AGENTE, None)
                stile.errore(e)

    r = st.session_state.get(AGENTE)
    if not r:
        return
    with st.chat_message("assistant", avatar=AVATAR["assistant"]):
        st.markdown(r["answer"])
    # Se SVEVA dice che un lotto costa 12 euro, chi legge deve poter vedere
    # che quel numero viene da una query e non dalla fantasia del modello.
    if r.get("passi"):
        with st.expander(f"Strumenti usati ({len(r['passi'])})", expanded=True):
            for i, passo in enumerate(r["passi"], 1):
                risultati = (f" → {passo['risultati']} risultati"
                             if passo.get("risultati") is not None else "")
                st.markdown(f"{i}. `{passo['strumento']}`{risultati}")
                st.code(json.dumps(passo["argomenti"], ensure_ascii=False), language="json")
    else:
        st.caption("Nessuno strumento usato: la risposta non contiene dati del catalogo.")
    stile.metriche(r.get("metriche"))


def pagina() -> None:
    _intestazione()
    modalita = st.segmented_control(
        "Modalità", ["conoscenza", "catalogo"], default="conoscenza", key="sveva_modalita",
        format_func={"conoscenza": "Conoscenza enologica", "catalogo": "Dati del catalogo"}.get,
        label_visibility="collapsed",
    ) or "conoscenza"

    if modalita == "conoscenza":
        _conoscenza()
    else:
        _catalogo()

    stile.nota(
        "<strong>Cosa esce dall'installazione.</strong> Le domande a SVEVA vengono inviate a un "
        "modello linguistico esterno (OpenRouter) insieme ai dati del lotto scelto e ai passaggi "
        "recuperati. La conversazione non viene salvata: vive in questa sessione e si chiude con "
        "la pagina. SVEVA non è un'enologa e non nomina vitigni: il dataset non li contiene."
    )
