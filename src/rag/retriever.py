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
        self, question: str, top_k: int = 3, strategia: str = "ibrida"
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

        if strategia == "semantica":
            return self._ranking_semantico(question, all_docs)[:top_k]
        if strategia == "lessicale":
            return self._ranking_lessicale(question, all_docs)[:top_k]

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
        return ordered[:top_k]

    def build_context(self, question: str, top_k: int = 3) -> str:
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
