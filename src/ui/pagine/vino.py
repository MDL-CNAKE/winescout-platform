"""Scheda di un singolo vino.

Tutte le schede lavorano sullo STESSO vino, senza doverlo riselezionare:
predizione, leve, conservazione, raccomandazioni, packaging, SVEVA e
selezione condivisa.
"""
import html

import pandas as pd
import streamlit as st

from src.ui import api, routing, stile
from src.ui.api import ApiError
from src.ui.disegni import bottiglia, radar
from src.ui.formato import abbinamenti, euro, livello_conservazione, lotto_vino, tipo_esteso, titolo_vino

GIUDIZIO_STILE = {
    "ottimo": st.success,
    "buono": st.success,
    "accettabile": st.warning,
    "sconsigliato": st.error,
}

LIVELLO_COLORE = {"buono": "green", "attenzione": "orange", "critico": "red"}


def _scegli_vino() -> int | None:
    try:
        sommario = api.vini_sommario()
    except ApiError as e:
        stile.errore(e)
        return None
    ids = [w["id"] for w in sommario]
    nomi = {w["id"]: w["name"] for w in sommario}
    scelto = st.session_state.get(routing.VINO_SCELTO, ids[0])
    indice = ids.index(scelto) if scelto in ids else 0
    nuovo = st.selectbox("Vino", ids, index=indice, format_func=nomi.get,
                         help="Scrivi per cercare fra i 6.497 lotti.")
    st.session_state[routing.VINO_SCELTO] = nuovo
    return nuovo


def _intestazione(v: dict) -> None:
    """Bottiglia disegnata dai dati accanto ai valori, come in React."""
    lotto = lotto_vino(v["name"])
    piatti = abbinamenti(v["food_pairing"])
    elenco = ""
    if piatti:
        elenco = ('<p class="vino-piatti-titolo">Abbinamenti consigliati</p><ul class="vino-piatti">'
                  + "".join(f"<li>{html.escape(p)}</li>" for p in piatti) + "</ul>")
    figura = bottiglia(v["id"], v["type"], v["quality"], v["alcohol"], v["residual_sugar"], altezza=230)
    stile.html(
        f'<div class="vino-hero"><div class="vino-figura">{figura}</div><div class="vino-meta">'
        f'<h2>{html.escape(titolo_vino(v["name"]))}</h2>'
        + (f'<span class="vino-lotto">Lotto {lotto}</span>' if lotto else "")
        + f'<div class="vino-dati"><span>{tipo_esteso(v["type"])}</span>'
        f'<span>{v["alcohol"]:.1f}% vol</span><span>pH {v["ph"]:.2f}</span>'
        f'<span>Qualità {v["quality"]}/10</span><span>{euro(v["price_eur"])}</span></div>'
        f'{elenco}</div></div>'
    )


def _tab_predizione(v: dict) -> None:
    st.caption(
        "Parametri precompilati con il profilo di questo vino: modificali per simulare "
        "come cambierebbe il punteggio previsto. Acido citrico, SO₂ e densità non sono "
        "esposti dalla scheda e partono da valori tipici per il tipo di vino."
    )
    rosso = v["type"] == "red"
    valori = {
        "fixed_acidity": ("Acidità fissa", v["fixed_acidity"], 0.1),
        "volatile_acidity": ("Acidità volatile", v["volatile_acidity"], 0.01),
        "citric_acid": ("Acido citrico", 0.3, 0.01),
        "residual_sugar": ("Zucchero residuo", v["residual_sugar"], 0.1),
        "chlorides": ("Cloruri", v["chlorides"], 0.001),
        "free_sulfur_dioxide": ("SO₂ libera", 15.0 if rosso else 35.0, 1.0),
        "total_sulfur_dioxide": ("SO₂ totale", 46.0 if rosso else 138.0, 1.0),
        "density": ("Densità", 0.996, 0.0001),
        "ph": ("pH", v["ph"], 0.01),
        "sulphates": ("Solfati", v["sulphates"], 0.01),
        "alcohol": ("Alcol %", v["alcohol"], 0.1),
    }
    with st.form(f"pred_{v['id']}"):
        colonne = st.columns(4)
        inseriti = {"type": v["type"]}
        for i, (campo, (etichetta, valore, passo)) in enumerate(valori.items()):
            formato = "%.4f" if passo < 0.001 else ("%.3f" if passo < 0.01 else "%.2f")
            inseriti[campo] = colonne[i % 4].number_input(
                etichetta, value=float(valore), step=passo, format=formato)
        invia = st.form_submit_button("Predici qualità", type="primary")

    if invia:
        try:
            st.session_state[f"pred_esito_{v['id']}"] = api.predici(inseriti)
        except ApiError as e:
            stile.errore(e)

    esito = st.session_state.get(f"pred_esito_{v['id']}")
    if esito is not None:
        c1, c2 = st.columns([1, 3])
        c1.metric("Punteggio previsto", f"{esito:.1f}/10",
                  delta=f"{esito - v['quality']:+.1f} rispetto al reale", delta_color="off")
        c2.caption(
            f"Qualità reale in catalogo: {v['quality']}/10. Lo scarto dipende da fattori non "
            "chimici (annata, terroir, affinamento) che il modello non osserva."
        )

    c1, c2 = st.columns([1, 1])
    with c1:
        stile.html(radar(v))
    c2.caption(
        "Profilo chimico normalizzato sui range tipici del dataset (0-100%), non valori "
        "assoluti: serve a confrontare la forma di vini diversi."
    )
    stile.nota(stile.NOTA_PREDIZIONE)


def _tab_leve(wine_id: int) -> None:
    try:
        dati = api.leve(wine_id)
    except ApiError as e:
        stile.errore(e)
        return

    st.markdown(
        f"Previsione attuale del modello: **{dati['previsione_attuale']:.2f}** su 10 "
        f"(qualità rilevata in catalogo: {dati['qualita_reale']}). Di seguito le correzioni "
        "che alzerebbero di più la stima, valutate una alla volta."
    )
    if not dati["leve"]:
        st.info(
            "Nessuna correzione a singolo parametro migliora la stima di questo lotto entro un "
            "intervento realistico. Non significa che il vino non sia migliorabile: secondo il "
            "modello il margine non sta in una singola leva."
        )
    else:
        massimo = dati["leve"][0]["delta_qualita"] or 1
        for leva in dati["leve"]:
            with st.container(border=True):
                azione = "Ridurre" if leva["direzione"] == "ridurre" else "Aumentare"
                c1, c2 = st.columns([4, 1])
                c1.markdown(
                    f"**{azione} {leva['etichetta'].lower()}** — {leva['valore_attuale']} → "
                    f"**{leva['valore_proposto']}** {leva['unita']}"
                )
                c2.markdown(f"<p style='text-align:right;font-weight:700;color:#6d1b2f'>"
                            f"+{leva['delta_qualita']:.2f}</p>", unsafe_allow_html=True)
                st.progress(max(0.04, leva["delta_qualita"] / massimo))
                st.caption(leva["intervento"])
    stile.nota(stile.NOTA_LEVE)


def _tab_conservazione(wine_id: int) -> None:
    try:
        dati = api.conservazione(wine_id)
    except ApiError as e:
        stile.errore(e)
        return

    livello = livello_conservazione(dati["punteggio"])
    c1, c2 = st.columns([1, 3])
    c1.metric("Indice di conservazione", f"{dati['punteggio']}/100")
    c2.markdown(f"### :{LIVELLO_COLORE[livello]}[{dati['giudizio']}]")

    for ind in dati["indicatori"]:
        colore = LIVELLO_COLORE.get(ind["livello"], "gray")
        with st.container(border=True):
            st.markdown(
                f"**{ind['nome']}** — {ind['valore']} {ind['unita']} · "
                f":{colore}[{ind['livello']}]"
            )
            st.caption(ind["spiegazione"])
    stile.nota(stile.NOTA_CONSERVAZIONE)


def _tab_raccomandazioni(wine_id: int) -> None:
    try:
        simili = api.raccomandazioni(wine_id)
        economici = api.alternative_economiche(wine_id)
    except ApiError as e:
        stile.errore(e)
        return

    st.subheader("Vini simili")
    st.dataframe(
        pd.DataFrame([{
            "Referenza": r["name"], "Tipo": tipo_esteso(r["type"]), "Alcol": r["alcohol"],
            "Qualità": r["quality"], "Prezzo": r["price_eur"], "Similarità": r["similarity"] * 100,
        } for r in simili]),
        hide_index=True, width="stretch",
        column_config={
            "Alcol": st.column_config.NumberColumn(format="%.1f%%"),
            "Prezzo": st.column_config.NumberColumn(format="%.2f €"),
            "Similarità": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
        },
    )

    st.subheader("Alternative più economiche")
    if not economici:
        st.info("Nessuna alternativa più economica fra i vini chimicamente simili.")
    else:
        st.dataframe(
            pd.DataFrame([{
                "Referenza": r["name"], "Prezzo": r["price_eur"],
                "Similarità": r["similarity"] * 100, "Risparmio": r["savings_pct"] * 100,
            } for r in economici]),
            hide_index=True, width="stretch",
            column_config={
                "Prezzo": st.column_config.NumberColumn(format="%.2f €"),
                "Similarità": st.column_config.NumberColumn(format="%.1f%%"),
                "Risparmio": st.column_config.NumberColumn(format="-%.1f%%"),
            },
        )
        st.caption(
            "Ordinato per un punteggio combinato: 70% similarità chimica, 30% risparmio, "
            "per privilegiare la coerenza del profilo gustativo sul solo prezzo."
        )
    stile.nota(stile.NOTA_RACCOMANDAZIONE)


def _tab_packaging(wine_id: int) -> None:
    try:
        p = api.packaging(wine_id)
    except ApiError as e:
        stile.errore(e)
        return
    c = st.columns(4)
    c[0].metric("Stile", p["style"])
    c[1].metric("Formato", p["bottle_format"])
    c[2].metric("Tappo", p["cap_type"])
    c[3].metric("Etichetta", p["label_material"])
    st.caption(
        "Il tappo segue la qualità, cioè la durata prevista del vino, non il colore: sughero "
        "naturale solo dove c'è qualcosa da far evolvere (qualità ≥ 7), vite per il consumo "
        "immediato. Nessun criterio usa la menzione 'Riserva', che il dataset non può giustificare."
    )


def _tab_sveva(v: dict) -> None:
    st.subheader("Valuta un abbinamento")
    st.caption(
        "SVEVA risponde con un oggetto validato: giudizio su una scala chiusa e un dato reale "
        "del vino a sostegno. Se il modello non rispetta lo schema, riceve l'errore e ritenta una volta."
    )
    with st.form(f"verdetto_{v['id']}"):
        piatto = st.text_input("Piatto", placeholder="Es: risotto ai funghi porcini")
        invia = st.form_submit_button("Valuta", type="primary")
    if invia and piatto.strip():
        with st.spinner("SVEVA sta valutando..."):
            try:
                # Chiave diversa da quella del form: Streamlit riserva la
                # chiave di un form al form stesso.
                st.session_state[f"esito_verdetto_{v['id']}"] = (piatto, api.verdetto(v["id"], piatto))
            except ApiError as e:
                stile.errore(e)

    salvato = st.session_state.get(f"esito_verdetto_{v['id']}")
    if salvato:
        piatto_salvato, r = salvato
        ver = r["verdetto"]
        GIUDIZIO_STILE.get(ver["giudizio"], st.info)(
            f"**{ver['giudizio'].capitalize()}** con {piatto_salvato}. {ver['motivazione']}"
        )
        st.markdown(f"Dato citato: `{ver['dato_citato']}`")
        if ver.get("profilo_alternativo"):
            st.markdown(f"Più indicato: {ver['profilo_alternativo']}")
        st.caption(f"Tentativi: {r['tentativi']}")
        stile.metriche(r.get("metriche"))
        st.caption(
            "Lo schema garantisce la forma, non la verità: confronta il dato citato con la "
            "scheda del vino qui sopra."
        )

    st.divider()
    st.subheader("Chiedi a SVEVA")
    st.caption(f"La risposta userà i dati reali di {v['name']} come contesto.")
    with st.form(f"domanda_{v['id']}"):
        domanda = st.text_area("Domanda", placeholder="Es: come lo presento a un cliente che "
                                                      "ha ordinato pesce alla griglia?")
        invia = st.form_submit_button("Chiedi a SVEVA", type="primary")
    if invia and domanda.strip():
        with st.spinner("SVEVA sta pensando..."):
            try:
                r = api.chiedi_sommelier(domanda, v["id"], [])
            except ApiError as e:
                stile.errore(e)
                return
        if r["demo_mode"]:
            st.warning("Modalità demo: chiave LLM non configurata, risposta generata dalle regole.")
        st.markdown(r["answer"])
        stile.metriche(r.get("metriche"))


def _tab_selezione(wine_id: int) -> None:
    operatore = st.session_state.get(routing.OPERATORE)
    try:
        tutti = api.preferiti()
    except ApiError as e:
        stile.errore(e)
        return
    chi = [p for p in tutti if p["wine_id"] == wine_id]
    if chi:
        st.markdown("Segnato da: " + ", ".join(p["operator_name"] for p in chi))
    else:
        st.caption("Nessun collega ha ancora segnato questo vino.")

    if operatore is None:
        st.info("Scegli chi sta lavorando nella barra laterale per segnare il vino.")
        return
    gia = any(p["operator_id"] == operatore for p in chi)
    try:
        if gia and st.button("Togli dalla mia selezione"):
            api.rimuovi_preferito(wine_id, operatore)
            st.rerun()
        if not gia and st.button("Aggiungi alla mia selezione", type="primary"):
            api.aggiungi_preferito(wine_id, operatore)
            st.rerun()
    except ApiError as e:
        stile.errore(e)


def pagina() -> None:
    wine_id = _scegli_vino()
    if wine_id is None:
        return
    try:
        v = api.vino(wine_id)
    except ApiError as e:
        stile.errore(e)
        return

    _intestazione(v)

    schede = st.tabs(["Predizione", "Leve", "Conservazione", "Raccomandazioni",
                      "Packaging", "SVEVA", "Selezione"])
    with schede[0]:
        _tab_predizione(v)
    with schede[1]:
        _tab_leve(wine_id)
    with schede[2]:
        _tab_conservazione(wine_id)
    with schede[3]:
        _tab_raccomandazioni(wine_id)
    with schede[4]:
        _tab_packaging(wine_id)
    with schede[5]:
        _tab_sveva(v)
    with schede[6]:
        _tab_selezione(wine_id)
