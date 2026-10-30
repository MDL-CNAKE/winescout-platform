"""Sezioni dichiarate ma non ancora disponibili: Spedizioni e Marketing.

Marketing e' diversa da un segnaposto: le funzioni mancano perche' i dati
non esistono. CruScout conosce la chimica dei lotti, non un solo ordine,
cliente o canale. Costruire comunque un cruscotto pieno di numeri plausibili
sarebbe lo stesso errore che il progetto rifiuta altrove (inventare vitigni).
Ogni voce quindi dichiara quale dato le servirebbe: la pagina e' una
specifica per la cantina, non un annuncio.
"""
import streamlit as st

from src.ui import routing

FUNZIONI_MARKETING = [
    ("Andamento del venduto", "Come si muovono ricavi e volumi nel tempo, per mese e per stagione.",
     "Registro ordini con data, referenza, quantità e importo. Nel database non esiste nessuna "
     "tabella di vendite.", "mancante"),
    ("Referenze che tirano", "Quali lotti si vendono davvero, non quali sono i migliori in analisi.",
     "Storico ordini per referenza. Ordinare per qualità e prezzo è un'altra cosa: un vino ottimo "
     "che nessuno compra resterebbe in cima.", "mancante"),
    ("Marginalità per fascia", "Dove si guadagna davvero, al netto dei volumi.",
     "Costi di produzione per lotto e quantità vendute. Il margine esistente è una stima "
     "derivata dal prezzo, non un margine misurato.", "parziale"),
    ("Canali di vendita", "Quanto pesano enoteca, ristorazione, vendita diretta e online.",
     "Un campo canale su ogni ordine. Il dato non è deducibile da nulla di ciò che la "
     "piattaforma conosce.", "mancante"),
    ("Composizione del catalogo", "Come si distribuisce l'offerta per fascia di prezzo, qualità e tipologia.",
     "Nulla: questi dati ci sono già. È l'unica analisi di questo elenco realizzabile oggi.", "parziale"),
    ("Stagionalità degli abbinamenti", "Quali abbinamenti vengono chiesti a SVEVA e in quale periodo.",
     "Registrazione delle domande poste al sommelier. Oggi non vengono salvate: scelta deliberata "
     "di riservatezza, da riconsiderare in modo esplicito.", "mancante"),
]


def marketing() -> None:
    st.title("Marketing e strategia")
    st.markdown(
        "Le analisi commerciali non ci sono ancora, e non per mancanza di tempo: la piattaforma "
        "conosce la chimica dei lotti, non le vendite. Per ciascuna è indicato il dato che "
        "servirebbe, così la cantina sa da dove cominciare."
    )
    colonne = st.columns(2)
    for i, (titolo, cosa, richiede, stato) in enumerate(FUNZIONI_MARKETING):
        with colonne[i % 2].container(border=True):
            etichetta = "Dato parziale" if stato == "parziale" else "Dato mancante"
            st.markdown(f"**{titolo}** <span class='badge badge-{stato}'>{etichetta}</span>",
                        unsafe_allow_html=True)
            st.markdown(cosa)
            st.caption(richiede)
    st.markdown(
        "Nel frattempo il catalogo si filtra ed esporta in CSV: i dati che la piattaforma "
        "possiede davvero sono già pronti per Excel, Power Query o pandas."
    )
    st.page_link(routing.PAGINE["catalogo"], label="Vai al catalogo", icon=":material/wine_bar:")


def spedizioni() -> None:
    st.title("Spedizioni")
    st.markdown("**In arrivo.** Qui troverai la preparazione degli ordini: cosa esce, in quale "
                "formato, con quale confezionamento e verso quale canale.")
    st.caption("Nel frattempo la pagina Packaging riporta formato, tappo ed etichetta di ogni "
               "lotto, e la pagina Conservazione indica quali lotti far partire per primi.")
    c1, c2 = st.columns(2)
    if "packaging" in routing.PAGINE:
        c1.page_link(routing.PAGINE["packaging"], label="Packaging", icon=":material/inventory_2:")
    if "conservazione" in routing.PAGINE:
        c2.page_link(routing.PAGINE["conservazione"], label="Conservazione", icon=":material/schedule:")
