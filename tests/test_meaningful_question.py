"""Test del filtro anti-gibberish davanti alle chiamate LLM.

QUESTI TEST SONO UNA DECISIONE DI PRODOTTO, NON UNA VERIFICA TECNICA.
`is_meaningful_question` e' un'euristica: non esiste una risposta "giusta"
calcolabile, esiste un confine che qualcuno ha scelto. Questi test scrivono
dove passa quel confine, cosi' che ritoccare una soglia in futuro faccia
fallire qualcosa invece di degradare l'esperienza in silenzio.

I due errori possibili non sono simmetrici:
- FALSO POSITIVO (passa gibberish) -> costa una chiamata a pagamento;
- FALSO NEGATIVO (blocca una domanda vera) -> costa un utente che non capisce
  perche' viene respinto.

Il secondo e' peggiore, quindi il filtro e' tarato permissivo. La classe
`TestDomandeLegittime` e' percio' la piu' importante del file: ogni suo
fallimento e' una persona respinta ingiustamente.
"""
import pytest

from backend.main import is_meaningful_question


class TestDomandeLegittime:
    """Casi che DEVONO passare. Un fallimento qui e' un utente respinto."""

    @pytest.mark.parametrize("testo", [
        # Il caso che ha motivato la riscrittura: il nome del piatto e basta
        # e' il modo piu' naturale di chiedere un abbinamento, e la versione
        # precedente del filtro lo rifiutava.
        "ndole",
        "carbonara",
        "tiramisu",
        "pesce",
        "curry",
        # Piatti non italiani: e' il punto piu' delicato del progetto. Il
        # retrieval ibrido esiste apposta per gestirli; se il filtro li
        # blocca prima, quel lavoro non serve a niente.
        "ndole con arachidi",
        "poke hawaiano",
        "kimchi",
        "couscous di pesce",
        # Domande brevi con punteggiatura.
        "che vino?",
        "con il pesce?",
        # Domande normali.
        "che vino abbino a una carbonara?",
        "cosa mi consigli per una cena di pesce",
        "questo lotto si conserva bene?",
        # Termini tecnici, che a un filtro ingenuo sembrano strani.
        "SO2 molecolare",
        "acidita volatile alta, che faccio?",
        "il pH e' 3.9, e' un problema?",
        # Consonanti fitte ma lecite: la soglia non deve tagliare l'italiano.
        "sgombro",
        "abbinamento per lo sgombro alla brace",
    ])
    def test_passa(self, testo):
        assert is_meaningful_question(testo) is True, (
            f"'{testo}' e' una domanda legittima ma viene rifiutata: "
            "un utente vedrebbe un rifiuto che non sa come correggere."
        )


class TestGibberish:
    """Casi che DEVONO essere bloccati prima di spendere una chiamata."""

    @pytest.mark.parametrize("testo", [
        # Carattere ripetuto.
        "kkkkkkkk",
        "aaaa",
        "!!!!!!",
        # Sequenze di tasti adiacenti: l'indizio piu' netto del pestare
        # tastiera, perche' nessuna lingua le produce.
        "qwerty",
        "asdfgh",
        "zxcvbn",
        "qwertyuiop",
        # Nessuna vocale: in italiano non esistono parole senza vocali.
        "jkljkl",
        "brrr",
        "zzz",
        # Nessuna lettera.
        "12345",
        "...",
        "?!?!?!",
        # Vuoto e spazi.
        "",
        "   ",
        # Troppo corto per essere qualcosa.
        "ab",
    ])
    def test_blocca(self, testo):
        assert is_meaningful_question(testo) is False, (
            f"'{testo}' non e' una domanda ma passa il filtro: "
            "verrebbe spesa una chiamata LLM a vuoto."
        )


class TestConfineDichiarato:
    """Casi ambigui, dove la scelta e' discutibile.

    Vengono messi per iscritto proprio perche' sono opinabili: se un giorno
    si decidesse diversamente, il test fallisce e obbliga a decidere di
    nuovo invece di lasciar cambiare il comportamento per caso.
    """

    def test_parola_singola_inventata_ma_pronunciabile_passa(self):
        """"Salatino" non esiste come piatto, ma e' pronunciabile e potrebbe
        essere un piatto regionale che non conosciamo. Il filtro non e' un
        dizionario: distinguere una parola vera da una inventata plausibile
        richiederebbe un modello, cioe' la chiamata che stiamo cercando di
        evitare. Passa, e sara' l'LLM a dire che non sa cosa sia."""
        assert is_meaningful_question("salatino") is True

    def test_consonanti_oltre_soglia_bloccate(self):
        """Cinque consonanti consecutive non esistono in nessuna lingua
        plausibile per questo pubblico. E' la soglia scelta: sotto passa, da
        qui in su no. La vocale finale serve a isolare il criterio: senza,
        la stringa verrebbe gia' bloccata dalla regola sulle vocali e il
        test non proverebbe quello che dice di provare."""
        assert is_meaningful_question("sgrmpfa") is False

    def test_quattro_consonanti_passano(self):
        """Quattro consonanti consecutive restano ammesse: esistono in
        tedesco e in diverse lingue africane, e bloccarle riporterebbe il
        bias culturale dalla porta di servizio."""
        assert is_meaningful_question("angst") is True
