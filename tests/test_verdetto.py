"""Test dello schema del verdetto di abbinamento.

Non chiamano l'LLM: verificano che il contratto regga davanti agli output
malformati che un modello produce realmente. E' il punto della feature —
lo schema serve proprio a rifiutare questi casi invece di propagarli
all'interfaccia.
"""
import json

import pytest
from pydantic import ValidationError

from backend.main import VerdettoAbbinamento, _estrai_json


VALIDO = {
    "giudizio": "buono",
    "motivazione": "L'acidita' sostiene la grassezza del piatto.",
    "dato_citato": "acidita' fissa 7,2 g/L",
    "profilo_alternativo": None,
}


def test_output_conforme_viene_accettato():
    v = VerdettoAbbinamento.model_validate(VALIDO)
    assert v.giudizio == "buono"
    assert v.profilo_alternativo is None


def test_giudizio_fuori_scala_viene_rifiutato():
    """Il modello inventa spesso sfumature intermedie ("discreto", "ok").

    Se le accettassimo, la scala smetterebbe di essere ordinabile e il
    campo tornerebbe a essere testo libero travestito da enumerazione.
    """
    with pytest.raises(ValidationError):
        VerdettoAbbinamento.model_validate({**VALIDO, "giudizio": "discreto"})


def test_dato_citato_vuoto_viene_rifiutato():
    """Un dato citato vuoto significa nessun ancoraggio ai numeri del lotto.

    E' esattamente il fallimento che questo campo esiste per intercettare:
    meglio ritentare che mostrare un verdetto senza appiglio.
    """
    with pytest.raises(ValidationError):
        VerdettoAbbinamento.model_validate({**VALIDO, "dato_citato": "   "})


def test_campo_mancante_viene_rifiutato():
    parziale = {k: v for k, v in VALIDO.items() if k != "motivazione"}
    with pytest.raises(ValidationError):
        VerdettoAbbinamento.model_validate(parziale)


def test_motivazione_troppo_lunga_viene_rifiutata():
    """Il limite di lunghezza e' un guardrail di interfaccia, non un vezzo:
    la scheda ha uno spazio finito e un muro di testo la rende inutile."""
    with pytest.raises(ValidationError):
        VerdettoAbbinamento.model_validate({**VALIDO, "motivazione": "a" * 500})


def test_json_incorniciato_da_testo_viene_recuperato():
    """Nonostante l'istruzione, i modelli avvolgono il JSON in ```json o in
    una frase di cortesia. Recuperare l'oggetto non e' una scorciatoia: il
    contenuto resta quello prodotto dal modello, si scarta solo la cornice."""
    grezzo = "Certo! Ecco la valutazione:\n```json\n" + json.dumps(VALIDO) + "\n```\nSpero sia utile."
    assert _estrai_json(grezzo)["giudizio"] == "buono"


def test_risposta_senza_json_solleva_errore():
    with pytest.raises(ValueError):
        _estrai_json("Mi dispiace, non posso valutare questo abbinamento.")
