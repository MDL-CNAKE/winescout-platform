"""Aspetto dell'interfaccia Streamlit e testi ricorrenti.

L'aspetto riprende il frontend React (frontend/src/index.css): fondo scuro
caldo con un alone in alto, pannello centrale traslucido, testo crema,
accenti oro. I colori di base stanno nel tema (.streamlit/config.toml); qui
ci sono le regole che il tema non copre: pannelli, card del catalogo,
navigazione, note di validazione.
"""
import streamlit as st

from src.ui.api import ApiError
from src.ui.formato import descrivi_metriche

_CSS = """
<style>
  :root {
    --bordeaux: #6d1b2f; --bordeaux-dark: #4a1220; --gold: #c9a24b;
    --gold-light: #e7d3a3; --cream: #f4ece2; --ink: #140810;
    --font-display: "Righteous", "Trebuchet MS", sans-serif;
  }

  /* Fondo scuro uniforme con un alone caldo in alto, come in React. */
  .stApp {
    background: radial-gradient(ellipse at 50% 0%, #2a1219 0%, transparent 55%), var(--ink);
    background-attachment: fixed;
  }
  [data-testid="stHeader"] { background: transparent; }

  /* Pannello centrale traslucido. */
  [data-testid="stMainBlockContainer"] {
    max-width: 1180px;
    background: rgba(26, 11, 16, 0.62);
    border: 1px solid rgba(231, 211, 163, 0.12);
    border-radius: 14px;
    margin-top: 1.25rem;
    margin-bottom: 2rem;
    padding: 2rem 2.4rem 2.5rem;
  }

  /* Titoli: oro per le pagine, crema per le sezioni. */
  h1 { color: var(--gold-light) !important; font-size: 2.1rem !important; }
  h2, h3 { color: var(--cream) !important; }
  [data-testid="stCaptionContainer"] { color: rgba(244, 236, 226, 0.55); }

  /* Barra laterale: navigazione a pulsanti, come la navbar di React. */
  [data-testid="stSidebar"] { border-right: 1px solid rgba(231, 211, 163, 0.25); }
  [data-testid="stSidebarNavLink"] {
    border: 1px solid rgba(244, 236, 226, 0.18);
    border-radius: 8px;
    margin-bottom: 0.3rem;
  }
  [data-testid="stSidebarNavLink"]:hover { border-color: var(--gold-light); }
  [data-testid="stSidebarNavLink"][aria-current="page"] {
    background: var(--gold-light);
    border-color: var(--gold-light);
  }
  [data-testid="stSidebarNavLink"][aria-current="page"] span { color: #2b1208 !important; font-weight: 600; }

  /* Pulsanti principali: fondo oro e testo scuro, leggibile sul fondo scuro. */
  [data-testid^="stBaseButton-primary"] { color: #2b1208 !important; font-weight: 600; }
  [data-testid^="stBaseButton-primary"] p { color: #2b1208 !important; }

  /* Metriche: valore in oro, come i numeri della trust strip di React. */
  [data-testid="stMetricValue"] { color: var(--gold-light); }

  /* Marchio. */
  .marchio { display: flex; align-items: center; gap: .6rem; }
  .marchio-parola { font-family: var(--font-display); font-size: 1.6rem; color: var(--cream); line-height: 1; }
  .marchio-parola em { font-style: normal; color: var(--gold-light); }
  .marchio-sotto { font-size: .62rem; letter-spacing: .26em; text-transform: uppercase;
                   color: rgba(244,236,226,.55); margin: .35rem 0 1rem 3.2rem; }

  /* Nota di validazione accanto al risultato che commenta. */
  .nota-validazione {
    margin: 1.5rem 0 .5rem; padding: .9rem 1.1rem;
    border-left: 3px solid rgba(231, 211, 163, .5); border-radius: 0 8px 8px 0;
    background: rgba(231, 211, 163, .07);
    font-size: .85rem; line-height: 1.6; color: rgba(244, 236, 226, .75);
  }
  .nota-validazione strong { color: var(--gold-light); }

  /* Card del catalogo. */
  .card-figura {
    display: flex; justify-content: center; padding: .5rem 0 .8rem; border-radius: 8px;
    background: radial-gradient(ellipse at center, rgba(231,211,163,.10) 0%, transparent 70%);
  }
  .card-figura svg { filter: drop-shadow(0 6px 14px rgba(0,0,0,.5)); }
  .card-riga { display: flex; justify-content: space-between; align-items: center; margin-bottom: .3rem; }
  .card-lotto { font-size: .68rem; letter-spacing: .12em; text-transform: uppercase; color: rgba(244,236,226,.5); }
  .card-colleghi span {
    display: inline-block; font-size: .62rem; font-weight: 700; color: #2b1208;
    background: var(--gold-light); border-radius: 999px; padding: .1rem .35rem; margin-left: .15rem;
  }
  .card-titolo { font-weight: 600; font-size: 1rem; line-height: 1.25; color: var(--cream); min-height: 2.5em; margin: 0 0 .4rem; }
  .card-desc {
    font-size: .78rem; line-height: 1.5; color: rgba(244,236,226,.6); margin: 0 0 .8rem;
    display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; min-height: 3.5em;
  }
  .card-prezzo {
    display: inline-block; background: rgba(255,255,255,.08); border-radius: 6px;
    padding: .3rem .6rem; font-weight: 600; font-size: .9rem; color: var(--cream); white-space: nowrap;
  }

  /* Intestazione della scheda vino. */
  .vino-hero { display: flex; gap: 1.8rem; align-items: flex-start; margin-bottom: .5rem; }
  .vino-figura {
    width: 170px; flex-shrink: 0; display: flex; justify-content: center; border-radius: 10px;
    background: radial-gradient(ellipse at center, rgba(231,211,163,.12) 0%, transparent 70%);
  }
  .vino-figura svg { filter: drop-shadow(0 10px 22px rgba(0,0,0,.55)); }
  .vino-meta h2 { margin: 0 0 .2rem; color: var(--gold-light) !important; font-size: 1.9rem; }
  .vino-lotto { color: rgba(244,236,226,.55); font-size: .85rem; letter-spacing: .1em; text-transform: uppercase; }
  .vino-dati { display: flex; flex-wrap: wrap; gap: .4rem 1.2rem; font-weight: 600; color: var(--gold-light); margin: .6rem 0 .9rem; }
  .vino-piatti { margin: 0; padding-left: 1.1rem; color: var(--cream); font-size: .92rem; }
  .vino-piatti-titolo { font-size: .75rem; letter-spacing: .14em; text-transform: uppercase; color: rgba(244,236,226,.55); margin: 0 0 .3rem; }

  /* Intestazione di SVEVA. */
  .sveva-testata { display: flex; align-items: center; gap: 2rem; margin-bottom: 1.2rem; }
  .sveva-nome { font-family: var(--font-display); font-size: 2.4rem; letter-spacing: .06em; color: var(--gold-light); line-height: 1; }
  .sveva-acronimo { font-size: .7rem; letter-spacing: .14em; text-transform: uppercase; color: var(--gold-light); margin: .4rem 0 .8rem; }
  .sveva-saluto { font-size: 1.05rem; line-height: 1.5; color: var(--cream); max-width: 46ch; margin: 0; }

  /* Etichette di stato nella pagina Marketing. */
  .badge { display: inline-block; padding: .12rem .55rem; border-radius: 999px; font-size: .72rem; font-weight: 600; margin-left: .4rem; }
  .badge-mancante { background: rgba(212,102,122,.2); color: #e88a9a; }
  .badge-parziale { background: rgba(231,211,163,.18); color: var(--gold-light); }

  /* Fascia di credibilita' in fondo al catalogo. */
  .fascia { display: flex; justify-content: center; gap: 3rem; flex-wrap: wrap;
            border-top: 1px solid rgba(231,211,163,.28); margin: 2.5rem auto .5rem; padding-top: 1.2rem; max-width: 680px; }
  .fascia div { display: flex; flex-direction: column; align-items: center; }
  .fascia b { font-size: 1.35rem; color: var(--gold-light); }
  .fascia span { font-size: .78rem; color: rgba(244,236,226,.6); }
  .fascia-fonte { text-align: center; font-size: .75rem; color: rgba(244,236,226,.45); }
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
    # Le righe vuote vanno tolte: per il parser markdown una riga vuota chiude
    # il blocco HTML, e il CSS dopo di essa verrebbe mostrato come testo.
    st.markdown("\n".join(r for r in _CSS.splitlines() if r.strip()), unsafe_allow_html=True)


def html(contenuto: str) -> None:
    st.markdown(contenuto, unsafe_allow_html=True)


def testa_sveva(larghezza: int = 42) -> str:
    return _TESTA_SVEVA.format(w=larghezza, h=round(larghezza * 0.86))


def marchio() -> None:
    """Marchio nella barra laterale: testa del sommelier accanto alla parola."""
    html(
        f'<div class="marchio">{testa_sveva(40)}'
        '<span class="marchio-parola">Cru<em>Scout</em></span></div>'
        '<p class="marchio-sotto">Il cruscotto del piccolo produttore</p>'
    )


def nota(testo_html: str) -> None:
    """Nota di validazione accanto al risultato che commenta.

    Il limite di un numero va detto dove il numero si legge: in fondo a un
    documento separato nessuno lo vede.
    """
    html(f'<div class="nota-validazione">{testo_html}</div>')


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
