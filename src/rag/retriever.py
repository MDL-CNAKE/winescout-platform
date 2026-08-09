"""Recupera dalla knowledge base i passaggi pertinenti a una domanda.

E' la fase di RETRIEVAL del RAG: la domanda dell'utente viene trasformata in
un embedding con lo STESSO modello usato per indicizzare i documenti (fase
obbligatoria: vettori prodotti da modelli diversi non sono confrontabili),
poi ChromaDB restituisce i documenti semanticamente piu vicini.

Il testo recuperato viene poi inserito nel prompt dell'LLM (fase di
AUGMENTED GENERATION), cosi la risposta si fonda su conoscenza verificata
invece che sulla sola memoria del modello, riducendo le allucinazioni.
"""
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR = "data/chroma"
COLLECTION = "enologia"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Quanti passaggi finiscono nel prompt. Non e' un numero di comodo: e' un
# compromesso fra copertura e costo, perche' ogni passaggio si paga a ogni
# domanda. E' stato scelto misurando (src/rag/evaluate.py):
#
#   top_k    hit rate@k
#     3         67%
#     4         75%
#     5         92%   <- ginocchio della curva
#     6         92%
#
# A 3 posti i documenti sensoriali venivano recuperati ma restavano in quarta
# e quinta posizione, dietro al documento sui piatti; a 6 non si guadagna piu'
# nulla e si paga contesto inutile.
TOP_K_PREDEFINITO = 5


class KnowledgeRetriever:
    """Ricerca semantica sulla knowledge base enologica.

    Il modello di embedding e il client ChromaDB vengono caricati una sola
    volta alla creazione dell'istanza: sono operazioni costose e vanno
    riusate (nell'app Streamlit l'istanza e' tenuta in cache).
    """

    def __init__(self) -> None:
        try:
            self.model = SentenceTransformer(MODEL_NAME)
            client = chromadb.PersistentClient(path=CHROMA_DIR)
            self.collection = client.get_collection(COLLECTION)
        except Exception as e:
            raise RuntimeError(
                f"Indice RAG non disponibile ({e}). "
                "Eseguire prima: python src/rag/build_index.py"
            ) from e

    # Parole troppo comuni per essere indizi utili nel match lessicale.
    STOPWORDS = {
        "che", "cosa", "come", "quale", "quali", "con", "per", "del", "della",
        "dei", "delle", "un", "una", "uno", "il", "lo", "la", "i", "gli", "le",
        "vino", "vini", "abbino", "abbinamento", "bevo", "bere", "piatto",
        "molto", "poco", "sono", "essere", "avere", "mio", "mia", "questo",
    }

    def _ranking_semantico(self, question: str, all_docs: list[str]) -> list[str]:
        """Ordina i chunk per vicinanza di significato (embedding)."""
        query_embedding = self.model.encode([question]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding, n_results=min(len(all_docs), 20)
        )
        return results["documents"][0] if results["documents"] else []

    def _ranking_lessicale(self, question: str, all_docs: list[str]) -> list[str]:
        """Ordina i chunk per presenza delle parole della domanda, pesate IDF."""
        keywords = {
            w.strip(".,;:!?'\"").lower()
            for w in question.split()
            if len(w) > 3 and w.strip(".,;:!?'\"").lower() not in self.STOPWORDS
        }
        # Confronto per RADICE (primi 5 caratteri) invece che per parola
        # esatta: l'italiano ha una morfologia ricca e "frittura" non
        # matcherebbe "fritti"/"fritture" presenti nella knowledge base.
        # E' uno stemming povero ma efficace su un vocabolario ristretto.
        lexical_scores: dict[str, float] = {}
        for kw in keywords:
            stem = kw[:5]
            matching = [d for d in all_docs if stem in d.lower()]
            if not matching:
                continue
            # Peso inversamente proporzionale alla diffusione del termine.
            weight = 1.0 / len(matching)
            for d in matching:
                lexical_scores[d] = lexical_scores.get(d, 0.0) + weight
        return sorted(lexical_scores, key=lexical_scores.get, reverse=True)

    def search(
        self, question: str, top_k: int = TOP_K_PREDEFINITO, strategia: str = "ibrida"
    ) -> list[str]:
        """Restituisce i top_k passaggi piu pertinenti con ricerca IBRIDA.

        Combina due strategie complementari:
        - SEMANTICA (embedding): coglie il significato anche quando le parole
          sono diverse ("frittura" trova un testo su "untuosita").
        - LESSICALE pesata per RARITA': promuove i chunk che contengono
          esattamente le parole della domanda, dando piu peso alle parole rare
          nella knowledge base. Il criterio e' quello dell'IDF (inverse
          document frequency): una parola presente in un solo chunk e' un
          indizio molto forte, una presente ovunque (es. "pesce") lo e' poco.

        La componente lessicale e' necessaria per una ragione documentata nei
        limiti del progetto: il modello di embedding multilingue e' addestrato
        prevalentemente su testi occidentali e non rappresenta correttamente i
        nomi di piatti extra-europei (es. "ndole"). Senza match lessicale il
        sistema fallirebbe proprio sulle cucine non occidentali, introducendo
        un bias culturale nelle raccomandazioni.

        I due ranking vengono fusi con Reciprocal Rank Fusion, cosi nessuna
        delle due strategie sovrasta sistematicamente l'altra.

        Args:
            question: domanda in linguaggio naturale (italiano).
            top_k: quanti chunk recuperare.
            strategia: "ibrida" (predefinita, usata in produzione), oppure
                "semantica" o "lessicale" per isolare una sola componente.
                Le due varianti isolate NON servono all'applicazione: esistono
                perche' senza poterle eseguire separatamente non si potrebbe
                misurare se la fusione porti un guadagno reale. Vedi
                src/rag/evaluate.py.

        Returns:
            Lista di testi della knowledge base, dal piu pertinente.
        """
        if not question or not question.strip():
            return []

        all_docs = self.collection.get()["documents"]

        # La diversificazione si applica a tutte e tre le strategie: se solo
        # l'ibrida ne beneficiasse, il confronto misurerebbe due differenze
        # insieme invece di isolare la fusione dei ranking.
        if strategia == "semantica":
            return self._diversifica(self._ranking_semantico(question, all_docs), top_k)
        if strategia == "lessicale":
            return self._diversifica(self._ranking_lessicale(question, all_docs), top_k)

        semantic = self._ranking_semantico(question, all_docs)
        lexical = self._ranking_lessicale(question, all_docs)

        # --- Fusione dei due ranking (Reciprocal Rank Fusion) ---
        K = 5  # costante di smorzamento: attenua il peso delle prime posizioni
        scores = {}
        for rank, doc in enumerate(semantic):
            scores[doc] = scores.get(doc, 0.0) + 1.0 / (K + rank)
        for rank, doc in enumerate(lexical):
            scores[doc] = scores.get(doc, 0.0) + 1.0 / (K + rank)

        ordered = sorted(scores, key=scores.get, reverse=True)
        return self._diversifica(ordered, top_k)

    def _diversifica(self, ordinati: list[str], top_k: int) -> list[str]:
        """Impedisce a un solo documento di occupare tutti i posti disponibili.

        PERCHE' SERVE, MISURATO. Con l'aggiunta del documento sui piatti
        comuni - lungo e diviso in molte sezioni, quindi molti chunk - una
        domanda come "cosa bevo con una carbonara?" riempiva tutti e tre i
        posti con chunk dello stesso documento. Il risultato apparente era
        ottimo (hit rate 100% contando quel documento come corretto) ma il
        recupero era peggiorato: l'LLM riceveva la scomposizione del piatto
        SENZA la regola di abbinamento che sta nel documento sensoriale.

        Il rilevamento e' stato possibile solo perche' la valutazione teneva
        ferma la ground truth originale: col solo criterio allargato il
        peggioramento sarebbe passato per un miglioramento.

        COME. Si scorre il ranking fuso e si accetta al massimo un chunk per
        documento finche' ci sono documenti diversi; se i posti avanzano si
        completa con i migliori rimasti. Un documento molto pertinente non
        viene quindi escluso, ma non puo' piu' monopolizzare il contesto.

        E' una forma minima di diversificazione dei risultati: la variante
        classica (Maximal Marginal Relevance) misura la ridondanza fra
        embedding, mentre qui basta il documento di provenienza, perche' la
        knowledge base e' fatta di pochi documenti tematici ben separati.
        """
        scelti: list[str] = []
        visti: set[str] = set()

        for chunk in ordinati:
            if len(scelti) >= top_k:
                break
            titolo = chunk.split("\n")[0]
            if titolo not in visti:
                scelti.append(chunk)
                visti.add(titolo)

        # Posti avanzati: si completa con i migliori scartati, mantenendo
        # l'ordine di rilevanza. Succede quando i documenti distinti sono
        # meno di top_k.
        if len(scelti) < top_k:
            for chunk in ordinati:
                if len(scelti) >= top_k:
                    break
                if chunk not in scelti:
                    scelti.append(chunk)

        return scelti

    def build_context(self, question: str, top_k: int = TOP_K_PREDEFINITO) -> str:
        """Restituisce i passaggi recuperati gia formattati per il prompt."""
        passages = self.search(question, top_k)
        if not passages:
            return ""
        joined = "\n\n---\n\n".join(passages)
        return (
            "Conoscenza enologica di riferimento (usa queste informazioni "
            f"per rispondere):\n\n{joined}"
        )


if __name__ == "__main__":
    # Test manuale: verifica che il retrieval trovi i documenti giusti.
    retriever = KnowledgeRetriever()

    domande = [
        "che vino abbino al ndole?",
        "cosa bevo con una frittura di pesce?",
        "che vino con un dolce al cioccolato?",
        "abbinamento per un piatto molto piccante",
    ]

    for d in domande:
        print(f"\n{'='*70}\nDOMANDA: {d}\n{'='*70}")
        for i, passage in enumerate(retriever.search(d, top_k=2), 1):
            titolo = passage.split("\n")[0]
            print(f"  {i}. {titolo}")
