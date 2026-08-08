"""Test delle regole di packaging e dell'endpoint che le espone.

Le quattro funzioni (_packaging_style, _bottle_format, _cap_type,
_label_material) sono deterministiche: stesso input, stesso output, nessuna
dipendenza esterna. Sono quindi il posto dove i test costano meno e rendono
di piu' — ed erano l'unica parte del progetto senza nemmeno uno.

La classe piu' importante non e' quella sui casi singoli ma
`TestTotalita`: verifica un INVARIANTE su tutte le combinazioni possibili,
invece di controllare qualche caso scelto a mano. Un test per caso conferma
cio' che si e' gia' pensato; un invariante intercetta anche quello a cui non
si e' pensato.
"""
import pytest
from fastapi.testclient import TestClient

import backend.main as backend_main
from backend.main import (
    _bottle_format,
    _cap_type,
    _label_material,
    _packaging_style,
)

STILI_ATTESI = {"Elegante", "Classico", "Moderno", "Young"}

# La qualita' nel dataset UCI sta fra 3 e 9; si allarga a 0-10 perche' la
# colonna e' un TINYINT e un valore fuori scala non deve far esplodere nulla.
QUALITA = range(0, 11)
PREZZI = [None, 0.0, 12.99, 13.0, 17.14, 34.29, 100.0]


class TestTotalita:
    """Ogni combinazione possibile deve produrre una scheda completa.

    E' il test che vale di piu': non controlla un risultato specifico ma che
    il sistema non abbia buchi. `_label_material` fa un accesso diretto a un
    dizionario e solleverebbe KeyError - cioe' un 500 in faccia all'utente -
    su qualsiasi stile non previsto. Oggi non succede; il test serve a
    scoprirlo subito il giorno in cui qualcuno aggiungera' uno stile senza
    aggiungere l'etichetta.
    """

    @pytest.mark.parametrize("quality", QUALITA)
    @pytest.mark.parametrize("price", PREZZI)
    def test_ogni_combinazione_produce_scheda_completa(self, quality, price):
        style = _packaging_style("Rosso", quality, price)
        assert style in STILI_ATTESI

        # Nessuna di queste deve sollevare: sono le quattro voci mostrate
        # nella scheda, e se una manca la pagina non si disegna.
        assert _label_material(style)
        assert _bottle_format("Rosso", quality)
        assert _cap_type("red", quality)
        assert _cap_type("white", quality)

    def test_tutti_gli_stili_sono_raggiungibili(self):
        """Se uno stile non fosse mai prodotto sarebbe codice morto: una
        regola scritta, documentata e mai applicata. Vale la pena saperlo."""
        prodotti = {
            _packaging_style("x", q, p) for q in QUALITA for p in PREZZI
        }
        assert prodotti == STILI_ATTESI, f"stili mai raggiunti: {STILI_ATTESI - prodotti}"


class TestStile:
    """L'ORDINE dei controlli e' la regola, non un dettaglio."""

    def test_alta_qualita_e_elegante_anche_se_costa_poco(self):
        """La qualita' viene valutata per prima: un lotto eccellente venduto
        a poco resta Elegante. E' una scelta deliberata - il packaging segue
        il vino, non il listino - e va messa per iscritto, perche' invertire
        i due controlli sembrerebbe innocuo e cambierebbe il risultato."""
        assert _packaging_style("x", 8, 5.0) == "Elegante"

    def test_prezzo_basso_declassa_solo_la_qualita_media(self):
        assert _packaging_style("x", 6, 12.0) == "Young"
        assert _packaging_style("x", 6, 13.0) == "Classico"

    def test_qualita_scarsa_e_sempre_young(self):
        assert _packaging_style("x", 4, 100.0) == "Young"

    def test_prezzo_assente_non_declassa(self):
        """price_eur e' NULL per i lotti non ancora prezzati. Un dato mancante
        non deve essere letto come 'economico': sarebbe trattare l'assenza di
        informazione come informazione."""
        assert _packaging_style("x", 6, None) == "Classico"

    def test_qualita_media_senza_sconto_e_moderno(self):
        assert _packaging_style("x", 5, 20.0) == "Moderno"


class TestFormatoETappo:

    def test_magnum_solo_per_i_migliori(self):
        assert _bottle_format("x", 8) == "Magnum 1.5L"
        assert _bottle_format("x", 7) == "Standard 750ml"

    def test_mignon_per_i_peggiori(self):
        assert _bottle_format("x", 4) == "Mignon 375ml"

    def test_bianco_di_pregio_prende_il_sughero(self):
        assert _cap_type("white", 7) == "Tappo in sughero naturale"
        assert _cap_type("white", 6) == "Tappo a vite"

    def test_rosso_scadente_prende_comunque_il_sughero(self):
        """Comportamento attuale, fissato qui perche' e' discutibile.

        Un rosso di qualita' 3 riceve mignon da 375ml, etichetta adesiva
        colorata e tappo in sughero naturale: il sughero costa piu' di tutto
        il resto della confezione. La regola dice 'rosso = sughero' senza
        guardare la qualita'.

        Il test non lo corregge - non e' una decisione tecnica ma commerciale,
        e la fa il titolare - ma lo rende visibile invece di lasciarlo
        sepolto in un `or`.
        """
        assert _cap_type("red", 3) == "Tappo in sughero naturale"


# ---------------------------------------------------------------------------
# L'endpoint
# ---------------------------------------------------------------------------

class FakeCursor:
    def __init__(self, riga):
        self._riga = riga

    def execute(self, *args, **kwargs):
        pass

    def fetchone(self):
        return self._riga

    def fetchall(self):
        return [self._riga] if self._riga else []

    def close(self):
        pass


class FakeConnection:
    def __init__(self, riga):
        self._riga = riga

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self, dictionary=False):
        return FakeCursor(self._riga)


@pytest.fixture
def client_con_vino(monkeypatch):
    riga = {
        "id": 1, "name": "Rosso Corposo", "type": "red",
        "quality": 7, "price_eur": 22.5,
    }
    monkeypatch.setattr(backend_main, "DatabaseConnection", lambda: FakeConnection(riga))
    monkeypatch.setattr(backend_main.joblib, "load", lambda path: None)
    monkeypatch.setattr(backend_main, "WineRecommender", lambda: None)
    monkeypatch.setattr(
        backend_main, "KnowledgeRetriever",
        lambda: (_ for _ in ()).throw(Exception("no index in test")),
    )
    with TestClient(backend_main.app) as c:
        yield c


@pytest.fixture
def client_senza_vino(monkeypatch):
    monkeypatch.setattr(backend_main, "DatabaseConnection", lambda: FakeConnection(None))
    monkeypatch.setattr(backend_main.joblib, "load", lambda path: None)
    monkeypatch.setattr(backend_main, "WineRecommender", lambda: None)
    monkeypatch.setattr(
        backend_main, "KnowledgeRetriever",
        lambda: (_ for _ in ()).throw(Exception("no index in test")),
    )
    with TestClient(backend_main.app) as c:
        yield c


def test_packaging_item_restituisce_scheda_completa(client_con_vino):
    r = client_con_vino.get("/api/packaging/1")
    assert r.status_code == 200
    dati = r.json()
    assert dati["style"] == "Elegante"
    assert dati["cap_type"] == "Tappo in sughero naturale"
    # Nessun campo vuoto: la scheda si disegna solo se ci sono tutte le voci.
    for campo in ("style", "bottle_format", "cap_type", "label_material"):
        assert dati[campo]


def test_packaging_item_inesistente_da_404(client_senza_vino):
    """404, non 500.

    La differenza non e' formale: 500 significa 'il server e' rotto' e manda
    a cercare un guasto che non c'e'; 404 significa 'quel lotto non esiste',
    che e' la verita' e non richiede alcun intervento.
    """
    r = client_senza_vino.get("/api/packaging/999999")
    assert r.status_code == 404


def test_packaging_item_id_non_numerico_da_422(client_con_vino):
    """FastAPI valida il tipo del parametro prima di eseguire la funzione:
    la query non parte nemmeno. E' la protezione che rende inutile un
    controllo manuale dentro l'endpoint."""
    r = client_con_vino.get("/api/packaging/abc")
    assert r.status_code == 422
