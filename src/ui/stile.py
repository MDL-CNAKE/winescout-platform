"""Elementi grafici e testi ricorrenti dell'interfaccia Streamlit.

I colori sono quelli del marchio, gli stessi del frontend React. I caratteri
restano quelli di sistema: la dichiarazione etica garantisce che il browser
non contatti terzi durante la navigazione, quindi niente font da CDN.
"""
import streamlit as st

from src.ui.api import ApiError
from src.ui.formato import descrivi_metriche

_CSS = """
<style>
  h1, h2, h3 { color: #4a1220; }
  .marchio { display: flex; align-items: center; gap: .6rem; margin-bottom: .2rem; }
  .marchio-parola { font-size: 1.5rem; font-weight: 700; color: #4a1220; letter-spacing: .3px; }
  .marchio-parola em { font-style: normal; color: #c9a24b; }
  .marchio-sotto { font-size: .8rem; color: #8a8177; margin: 0 0 1rem 0; }
  .nota-validazione {
    border-left: 3px solid #6d1b2f; background: #f4ece2;
    padding: .75rem 1rem; border-radius: 0 6px 6px 0;
    font-size: .9rem; color: #3a3a3a; margin: 1rem 0; line-height: 1.5;
  }
  .badge { display: inline-block; padding: .15rem .6rem; border-radius: 999px;
           font-size: .8rem; font-weight: 600; }
  .badge-mancante { background: #f7c1c1; color: #791f1f; }
  .badge-parziale { background: #fac775; color: #633806; }
</style>
"""

# La testa del sommelier, stessa forma di frontend/src/components/RobotSommelierIcon.tsx.
_TESTA_SVEVA = """
<svg viewBox="50 12 100 86" width="{w}" height="{h}" aria-hidden="true">
  <ellipse cx="100" cy="55" rx="46" ry="38" fill="#2a1015" stroke="#c9a24b" stroke-width="4"/>
  <ellipse cx="108" cy="55" rx="20" ry="16" fill="#f3e6cf"/>
  <circle cx="72" cy="45" r="4" fill="#c9a24b"/>
  <circle cx="72" cy="58" r="4" fill="#e8d98a"/>
  <circle cx="72" cy="71" r="4" fill="#6d1b2f"/>
</svg>
"""


def applica_stile() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def testa_sveva(larghezza: int = 42) -> str:
    return _TESTA_SVEVA.format(w=larghezza, h=round(larghezza * 0.86))


def marchio() -> None:
    """Marchio nella barra laterale: testa del sommelier accanto alla parola."""
    st.markdown(
        f'<div class="marchio">{testa_sveva(40)}'
        '<span class="marchio-parola">Cru<em>Scout</em></span></div>'
        '<p class="marchio-sotto">Il cruscotto del piccolo produttore</p>',
        unsafe_allow_html=True,
    )


def nota(testo_html: str) -> None:
    """Nota di validazione accanto al risultato che commenta.

    Il limite di un numero va detto dove il numero si legge: in fondo a un
    documento separato nessuno lo vede.
    """
    st.markdown(f'<div class="nota-validazione">{testo_html}</div>', unsafe_allow_html=True)


def errore(e: ApiError) -> None:
    # 503 = funzione che richiede la chiave LLM: non e' un guasto, e'
    # una configurazione mancante, quindi non va mostrata come errore rosso.
    if e.stato == 503:
        st.info(str(e))
    else:
        st.error(str(e))


def metriche(dati: dict | None) -> None:
    testo = descrivi_metriche(dati)
    if testo:
        st.caption(testo)


# --------------------------------------------------------------------------
# Testi delle note di validazione. Sono gli stessi di
# frontend/src/components/ValidationNote.tsx, con i valori corretti dopo la
# scoperta del leakage (vedi docs/model_limitations.md).
# --------------------------------------------------------------------------

NOTA_PREDIZIONE = (
    "<strong>Come leggere questo punteggio.</strong> RandomForest addestrato su 6.497 vini, "
    "validato con 5-fold cross-validation raggruppata (R² medio 0,39) e su un test set del "
    "20% senza righe ripetute (R² 0,40; RMSE 0,68). Il modello spiega circa il 40% della "
    "variabilità: coglie la tendenza generale, molto meno gli estremi della scala, dove il "
    "dataset contiene pochissimi esempi — il 77% dei vini sta in due sole classi. È un "
    "supporto decisionale, non sostituisce il giudizio di un sommelier."
)

NOTA_RACCOMANDAZIONE = (
    "<strong>Su cosa si basano.</strong> Similarità coseno sulle sole feature chimiche dei "
    "6.497 vini: il sistema propone vini con profilo analitico vicino, non vini che uno "
    "stesso cliente ha gradito. Annata, terroir e affinamento non sono nei dati e non entrano "
    "nel calcolo."
)

NOTA_LEVE = (
    "<strong>Come leggere queste stime.</strong> Sono simulazioni sul modello, non garanzie: "
    "ogni parametro viene mosso da solo, tenendo fermi gli altri. In cantina le variabili "
    "chimiche sono legate fra loro, quindi il guadagno reale sarà di solito inferiore. Il "
    "modello ha R² 0,40 sul test set senza righe ripetute: coglie la tendenza, non è un "
    "oracolo. I passi proposti sono correzioni realizzabili in una lavorazione reale."
)

NOTA_CONSERVAZIONE = (
    "<strong>Su cosa si basa.</strong> Quattro parametri enologici: SO₂ molecolare (la "
    "frazione di solforosa realmente attiva, calcolata da SO₂ libera e pH), acidità volatile "
    "rispetto ai limiti di legge UE, pH e quota di solforosa ancora libera. È un sistema a "
    "regole, non un modello addestrato: il dataset non contiene informazioni sull'evoluzione "
    "dei vini nel tempo. Riguarda la stabilità chimica, non il potenziale di invecchiamento."
)

NOTA_SIMULATI = (
    "Prezzo e margine sono <strong>simulati</strong> con una logica di business dichiarata "
    "(src/pricing.py): il dataset UCI non contiene dati commerciali."
)
