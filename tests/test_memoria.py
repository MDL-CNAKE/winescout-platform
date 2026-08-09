"""Test della memoria conversazionale: finestra scorrevole e query di recupero.

Sono due politiche, non due algoritmi: decidono COSA il modello ricorda e COSA
il retriever cerca. Entrambe sono invisibili all'utente, e le cose invisibili
vanno fissate per iscritto, altrimenti cambiano senza che nessuno se ne
accorga finche' qualcuno non si lamenta che "SVEVA ha dimenticato".
"""
import pytest

from backend.main import (
    BUDGET_CARATTERI_STORICO,
    MAX_MESSAGGI_STORICO,
    Messaggio,
    _finestra_scorrevole,
    _query_di_recupero,
)


def utente(testo: str) -> Messaggio:
    return Messaggio(ruolo="user", contenuto=testo)


def sveva(testo: str) -> Messaggio:
    return Messaggio(ruolo="assistant", contenuto=testo)


class TestFinestraScorrevole:
    """Il contesto e' finito e ogni token si ripaga a ogni turno."""

    def test_conversazione_corta_passa_intera(self):
        storico = [utente("che vino con la carbonara?"), sveva("un bianco strutturato")]
        assert _finestra_scorrevole(storico) == storico

    def test_storico_vuoto(self):
        assert _finestra_scorrevole([]) == []

    def test_tiene_i_messaggi_piu_recenti(self):
        """Si scarta dall'inizio della conversazione, non dalla fine.

        In un dialogo di abbinamento il valore dell'informazione decade in
        fretta: il piatto nominato due turni fa conta, quello di dieci no.
        Se si scartasse dal fondo, SVEVA ricorderebbe l'inizio e dimenticherebbe
        la domanda appena fatta - cioe' il contrario di cio' che serve.
        """
        storico = [utente(f"domanda {i}") for i in range(10)]
        finestra = _finestra_scorrevole(storico)

        assert len(finestra) == MAX_MESSAGGI_STORICO
        assert finestra[-1].contenuto == "domanda 9"
        assert finestra[0].contenuto == "domanda 4"

    def test_ordine_cronologico_preservato(self):
        """La finestra viene costruita a ritroso ma deve tornare in ordine:
        un modello legge i messaggi come una sequenza temporale, e invertirli
        cambierebbe il senso della conversazione."""
        storico = [utente(f"m{i}") for i in range(10)]
        finestra = _finestra_scorrevole(storico)
        assert [m.contenuto for m in finestra] == ["m4", "m5", "m6", "m7", "m8", "m9"]

    def test_budget_caratteri_taglia_prima_del_numero_di_messaggi(self):
        """Contare i messaggi senza contare la lunghezza e' una protezione
        finta: basta una risposta lunga perche' pochi messaggi diventino un
        prompt enorme. Qui due messaggi sono gia' oltre il budget, e la
        finestra deve fermarsi anche se il numero di messaggi lo consente."""
        lungo = "x" * (BUDGET_CARATTERI_STORICO // 2 + 100)
        storico = [utente(lungo), sveva(lungo), utente("e con il pesce?")]

        finestra = _finestra_scorrevole(storico)

        assert len(finestra) < len(storico)
        assert sum(len(m.contenuto) for m in finestra) <= BUDGET_CARATTERI_STORICO
        # Il messaggio piu' recente sopravvive sempre: e' quello a cui la
        # domanda corrente si riferisce.
        assert finestra[-1].contenuto == "e con il pesce?"

    def test_un_singolo_messaggio_enorme_non_passa(self):
        """Caso limite: un solo messaggio piu' grande dell'intero budget.
        Deve essere scartato, non troncato a meta' - un testo tagliato in
        mezzo a una frase confonde il modello piu' di quanto lo aiuti."""
        enorme = "x" * (BUDGET_CARATTERI_STORICO + 1)
        assert _finestra_scorrevole([utente(enorme)]) == []


class TestQueryDiRecupero:
    """Cosa viene cercato nella knowledge base, che NON e' cio' che l'utente
    ha scritto.

    E' il punto meno ovvio della funzionalita': dare memoria al modello e
    dimenticarsene per il recupero peggiora il RAG proprio quando la
    conversazione diventa naturale.
    """

    def test_domanda_autonoma_resta_intatta(self):
        domanda = "che vino abbino a una frittura di pesce?"
        assert _query_di_recupero(domanda, []) == domanda

    def test_seguito_corto_eredita_la_domanda_precedente(self):
        """'e con il pesce?' come query di ricerca non contiene quasi nulla
        di cercabile, e il retrieval ibrido - che si regge anche sulla
        corrispondenza lessicale - resterebbe senza appigli."""
        storico = [
            utente("che vino con una carbonara?"),
            sveva("un bianco strutturato"),
        ]
        query = _query_di_recupero("e con il pesce?", storico)

        assert "carbonara" in query
        assert "pesce" in query

    def test_seguito_senza_storico_resta_se_stesso(self):
        """Primo messaggio della conversazione: non c'e' nulla da ereditare."""
        assert _query_di_recupero("e con il pesce?", []) == "e con il pesce?"

    def test_eredita_solo_dai_messaggi_dell_utente(self):
        """Le risposte di SVEVA non entrano nella query.

        Sono testo generato: contengono termini enologici che il retriever
        troverebbe facilmente, e la ricerca finirebbe per inseguire le parole
        del modello invece di quelle di chi domanda. Il recupero si ancora a
        cio' che l'utente ha chiesto, non a cio' che il sistema ha risposto.
        """
        storico = [
            utente("che vino con la carbonara?"),
            sveva("serve acidita' e sapidita', magari un metodo classico"),
        ]
        query = _query_di_recupero("e col pesce?", storico)

        assert "carbonara" in query
        assert "metodo classico" not in query

    @pytest.mark.parametrize("domanda", [
        "abbinamento per una frittura di paranza croccante",
        "questo lotto si conserva bene nel tempo o no?",
    ])
    def test_domande_lunghe_non_trascinano_contesto(self, domanda):
        """Una domanda che si regge da sola non deve ereditare nulla:
        trascinare il contesto precedente sposterebbe la ricerca su un
        argomento che l'utente ha appena abbandonato."""
        storico = [utente("che vino con la carbonara?")]
        assert _query_di_recupero(domanda, storico) == domanda


class TestLimiteDichiarato:

    def test_cambio_di_argomento_con_domanda_corta_trascina_contesto(self):
        """Il limite noto dell'euristica, messo per iscritto.

        Se l'utente cambia argomento con una domanda breve, la query trascina
        un contesto ormai superato. La soluzione completa sarebbe far
        riformulare il seguito al modello (query condensation), al prezzo di
        una chiamata in piu' prima di OGNI recupero.

        Il test non certifica che il comportamento sia giusto: certifica che
        e' noto. Se un giorno si adottera' la riformulazione, questo test
        fallira' e sara' il promemoria del perche' si era scelto altro.
        """
        storico = [utente("che vino con la carbonara?")]
        query = _query_di_recupero("e il pH?", storico)
        assert "carbonara" in query
