"""Costruisce l'indice vettoriale ChromaDB dalla knowledge base enologica.

Come funziona il RAG (Retrieval-Augmented Generation):
1. I documenti vengono spezzati in CHUNK (paragrafi) e ognuno viene
   trasformato in un EMBEDDING, cioe' un vettore numerico che ne
   rappresenta il significato semantico.
2. Gli embedding vengono salvati in un VECTOR STORE (ChromaDB), database
   ottimizzato per la ricerca per similarita.
3. A runtime la domanda dell'utente viene trasformata nello stesso modo e
   ChromaDB restituisce i chunk semanticamente piu vicini, che finiscono nel
   prompt dell'LLM come contesto (vedi src/rag/retriever.py).

PERCHE' IL CHUNKING: indicizzare un intero documento come vettore unico
"diluisce" il significato (un testo che parla di amaro E piccante produce un
vettore intermedio, poco preciso per entrambi i temi). Spezzando in paragrafi,
ogni concetto ha un proprio vettore dedicato e la ricerca diventa molto piu
accurata. Il titolo del documento viene ripetuto in testa a ogni chunk per
non perdere il contesto di appartenenza.

Il modello di embedding e' multilingue perche' sia la knowledge base sia le
domande degli utenti sono in italiano.

Uso: python src/rag/build_index.py
"""
import sys
import os
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import chromadb
from sentence_transformers import SentenceTransformer

KB_DIR = Path("docs/knowledge_base")
CHROMA_DIR = "data/chroma"
COLLECTION = "enologia"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MIN_CHUNK_CHARS = 80  # sotto questa soglia il paragrafo viene accorpato


def chunk_document(text: str, title: str) -> list[str]:
    """Spezza un documento in chunk per paragrafo.

    Ogni chunk viene prefissato dal titolo del documento per conservare il
    contesto: senza, un paragrafo isolato perderebbe il tema di appartenenza.
    I paragrafi troppo corti vengono accorpati al successivo per evitare
    chunk poco informativi.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, buffer = [], ""

    for p in paragraphs:
        if p.startswith("#"):  # il titolo non diventa un chunk a se stante
            continue
        buffer = f"{buffer}\n\n{p}".strip() if buffer else p
        if len(buffer) >= MIN_CHUNK_CHARS:
            chunks.append(f"{title}\n\n{buffer}")
            buffer = ""

    if buffer:  # residuo finale
        chunks.append(f"{title}\n\n{buffer}")
    return chunks


def load_chunks() -> tuple[list[str], list[str]]:
    """Legge la knowledge base e la spezza in chunk indicizzabili."""
    if not KB_DIR.exists():
        raise RuntimeError(f"Knowledge base non trovata in {KB_DIR}")

    files = sorted(KB_DIR.glob("*.md"))
    if not files:
        raise RuntimeError(f"Nessun file .md trovato in {KB_DIR}")

    texts, ids = [], []
    for f in files:
        content = f.read_text(encoding="utf-8")
        title = content.split("\n")[0].lstrip("# ").strip()
        for i, chunk in enumerate(chunk_document(content, title)):
            texts.append(chunk)
            ids.append(f"{f.stem}__{i}")
    return texts, ids


def main() -> None:
    texts, ids = load_chunks()
    print(f"Knowledge base spezzata in {len(texts)} chunk")

    print(f"Caricamento modello di embedding ({MODEL_NAME})...")
    model = SentenceTransformer(MODEL_NAME)

    print("Calcolo degli embedding...")
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Ricrea la collection da zero: rilanciando lo script dopo aver
    # modificato la knowledge base, l'indice resta allineato.
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION)

    collection.add(documents=texts, embeddings=embeddings, ids=ids)
    print(f"OK: indicizzati {collection.count()} chunk in {CHROMA_DIR}")


if __name__ == "__main__":
    main()
