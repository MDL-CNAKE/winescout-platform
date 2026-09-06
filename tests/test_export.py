"""Test dell'export CSV del catalogo.

Il valore di questi test non e' verificare che il CSV si generi - lo si vede
aprendo il file - ma fissare i due comportamenti che si rompono in silenzio:

1. L'export deve applicare GLI STESSI filtri della ricerca. Se le due
   implementazioni divergessero, chi scarica otterrebbe un file diverso da
   cio' che ha visto a schermo e non avrebbe modo di accorgersene. Per questo
   la clausola WHERE e' costruita da una funzione sola, e qui si verifica che
   lo sia davvero.

2. Il formato italiano deve restare italiano. Excel in configurazione italiana
   usa il punto e virgola come separatore di colonna e la virgola come
   decimale: un CSV "standard" aperto su un computer italiano finisce tutto
   in una colonna e sembra rotto. E' un dettaglio che nessuno ricontrolla
   dopo averlo sistemato una volta.
"""
import pytest
from fastapi.testclient import TestClient

import backend.main as backend_main
from backend.main import _filtri_catalogo


class FakeCursor:
    """Registra le query eseguite, per poter verificare i filtri applicati."""

    def __init__(self, registro, righe):
        self.registro = registro
        self.righe = righe

    def execute(self, sql, params=None):
        self.registro.append((sql, list(params or [])))

    def fetchall(self):
        return self.righe

    def fetchone(self):
        return {"n": len(self.righe)}

    def close(self):
        pass


class FakeConnection:
    def __init__(self, registro, righe):
        self.registro = registro
        self.righe = righe

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self, dictionary=False):
        return FakeCursor(self.registro, self.righe)


RIGA = {
    "id": 1, "name": "Rosso Corposo", "type": "red", "alcohol": 12.5,
    "ph": 3.35, "residual_sugar": 2.1, "fixed_acidity": 7.2,
    "volatile_acidity": 0.28, "chlorides": 0.045, "sulphates": 0.62,
    "quality": 7, "price_eur": 22.5, "margin_pct": 31.0,
    "food_pairing": "Carni rosse alla brace",
}


@pytest.fixture
def registro():
    return []


@pytest.fixture
def client(monkeypatch, registro):
    monkeypatch.setattr(
        backend_main, "DatabaseConnection", lambda: FakeConnection(registro, [RIGA])
    )
    monkeypatch.setattr(backend_main.joblib, "load", lambda path: None)
    monkeypatch.setattr(backend_main, "WineRecommender", lambda: None)
    monkeypatch.setattr(
        backend_main, "KnowledgeRetriever",
        lambda: (_ for _ in ()).throw(Exception("no index in test")),
    )
    with TestClient(backend_main.app) as c:
        yield c


class TestFiltriCondivisi:
    """La clausola WHERE e' una sola, e deve restare tale."""

    def test_nessun_filtro_nessuna_clausola(self):
        where, params = _filtri_catalogo(*[None] * 10)
        assert where == ""
        assert params == []

    def test_filtri_multipli_in_and(self):
        where, params = _filtri_catalogo(
            "red", 6, None, None, None, None, None, None, None, 15.0
        )
        assert where.startswith("WHERE ")
        assert where.count(" AND ") == 2
        assert params == ["red", 6, 15.0]

    def test_tipo_non_valido_rifiutato(self):
        """Il valore finisce in una query parametrizzata, quindi non c'e'
        rischio di injection: il controllo serve a restituire 400 invece di
        un risultato vuoto silenzioso, che sembrerebbe un catalogo vuoto."""
        with pytest.raises(backend_main.HTTPException) as e:
            _filtri_catalogo("rosato", *[None] * 9)
        assert e.value.status_code == 400

    def test_export_e_ricerca_producono_gli_stessi_filtri(self, client, registro):
        """Il test che giustifica l'intero refactoring.

        Stessi parametri sulle due rotte devono produrre la stessa clausola
        WHERE e gli stessi valori. Se qualcuno aggiungesse un filtro solo
        alla ricerca, qui salterebbe.
        """
        q = "type=red&min_quality=6&max_price=25"

        client.get(f"/api/wines/search?{q}")
        sql_ricerca = [s for s, _ in registro if "SELECT COUNT" not in s]
        params_ricerca = [p for s, p in registro if "SELECT COUNT" not in s]
        registro.clear()

        client.get(f"/api/wines/export.csv?{q}")
        sql_export = [s for s, _ in registro]
        params_export = [p for s, p in registro]

        where_ricerca = sql_ricerca[0].split("WHERE")[1].split("ORDER BY")[0]
        where_export = sql_export[0].split("WHERE")[1].split("ORDER BY")[0]
        assert where_ricerca == where_export

        # La ricerca aggiunge LIMIT e OFFSET, l'export solo LIMIT: si
        # confrontano i soli valori dei filtri.
        assert params_ricerca[0][:3] == params_export[0][:3] == ["red", 6, 25.0]


class TestFormatoCSV:

    def test_formato_italiano_usa_punto_e_virgola_e_virgola_decimale(self, client):
        r = client.get("/api/wines/export.csv?formato=it")
        assert r.status_code == 200
        testo = r.text

        assert "Alcol (% vol)" in testo
        assert ";" in testo
        # 12.5 deve diventare 12,5: e' il punto dell'intera opzione.
        assert "12,5" in testo
        assert "12.5" not in testo

    def test_formato_internazionale_usa_virgola_e_punto_decimale(self, client):
        r = client.get("/api/wines/export.csv?formato=en")
        testo = r.text

        assert "12.5" in testo
        # Con separatore virgola, un decimale con la virgola spaccherebbe la
        # riga in due colonne.
        assert "12,5" not in testo

    def test_bom_presente(self, client):
        """Senza BOM Excel legge il file con la codifica locale e le lettere
        accentate arrivano illeggibili. E' invisibile finche' qualcuno non
        apre il file su Windows."""
        r = client.get("/api/wines/export.csv")
        assert r.content.startswith(b"\xef\xbb\xbf")

    def test_intestazione_di_download_col_nome_file(self, client):
        r = client.get("/api/wines/export.csv")
        assert "attachment" in r.headers["content-disposition"]
        assert ".csv" in r.headers["content-disposition"]

    def test_numero_righe_dichiarato(self, client):
        """Chi scarica puo' confrontare subito questo numero con il totale
        visto a schermo."""
        r = client.get("/api/wines/export.csv")
        assert r.headers["x-righe-esportate"] == "1"

    def test_formato_non_valido_rifiutato(self, client):
        assert client.get("/api/wines/export.csv?formato=de").status_code == 400

    def test_ordinamento_non_valido_rifiutato(self, client):
        assert client.get("/api/wines/export.csv?sort=a_caso").status_code == 400


def test_export_non_confuso_con_un_id(client):
    """`/api/wines/export.csv` sta PRIMA di `/api/wines/{wine_id}` nelle
    rotte: invertendole, FastAPI proverebbe a interpretare "export.csv" come
    un intero e restituirebbe 422. E' un errore che si introduce spostando
    codice, senza accorgersene."""
    r = client.get("/api/wines/export.csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
