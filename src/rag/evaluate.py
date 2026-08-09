"""Valutazione misurata del retrieval RAG.

PERCHE' ESISTE QUESTO FILE
--------------------------
Il retrieval ibrido (semantico + lessicale IDF fusi con Reciprocal Rank
Fusion) e' stato costruito su un'ipotesi ragionevole: il modello di embedding
multilingue non rappresenta bene i nomi di piatti extra-europei, quindi senza
componente lessicale il sistema fallirebbe sulle cucine non occidentali.

Ragionevole non vuol dire verificata. Finora l'unico controllo era stampare i
titoli recuperati e guardarli: sufficiente per accorgersi che qualcosa e'
rotto, non per sostenere che l'ibrido sia migliore del semantico puro. Se il
semantico da solo facesse lo stesso lavoro, il codice lessicale sarebbe
complessita' non giustificata e andrebbe rimosso.

COSA SI MISURA
--------------
Ogni domanda dichiara il documento che DOVREBBE essere recuperato (ground
truth). Su questa base si calcolano due indicatori complementari:

- HIT RATE@k — in quale frazione di domande il documento atteso compare fra i
  primi k risultati. Risponde a "il contesto giusto e' finito nel prompt?".
  E' la domanda giusta perche' l'LLM legge tutti i k passaggi, non solo il
  primo: se il documento corretto e' terzo su tre, il modello lo vede lo
  stesso.

- MRR (Mean Reciprocal Rank) — media di 1/posizione del primo documento
  corretto. Distingue casi che l'hit rate confonde: corretto in prima
  posizione vale 1.0, in terza vale 0.33. Serve perche' la posizione conta
  comunque: il contesto in cima occupa piu' attenzione del modello, e con un
  top_k piu' stretto sopravvive solo cio' che sta in alto.

I due numeri vanno letti insieme. Hit rate alto e MRR basso significa che il
sistema trova il documento giusto ma lo mette dietro a rumore: funziona oggi,
si rompe se si riduce k.

LIMITE DICHIARATO
-----------------
L'insieme di domande e' piccolo (scritto a mano) e la ground truth e' scelta
da chi ha scritto la knowledge base. Su una dozzina di domande una differenza
di pochi punti percentuali non e' significativa: questi numeri servono a
smascherare fallimenti netti, non a certificare un ottimo. E' una misura
onesta della sua portata, non una validazione statistica.

Uso: python src/rag/evaluate.py
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.rag.retriever import KnowledgeRetriever


# Ogni voce: (domanda, frammento del titolo del documento atteso).
# Il confronto avviene sul titolo perche' e' prefisso di ogni chunk (vedi
# build_index.chunk_document): identifica il documento senza dipendere da
# come i paragrafi sono stati spezzati.
DOMANDE = [
    # --- Casi in cui le parole della domanda NON compaiono nella KB:
    #     qui puo' funzionare solo la componente semantica.
    ("cosa bevo con una carbonara?", "Grassezza"),
    ("che vino con una bistecca al sangue?", "Sapidita"),
    ("abbinamento per un tiramisu", "Dolcezza"),
    ("vino per un piatto molto speziato che brucia", "amara"),
    ("che vino sta bene con il radicchio?", "amara"),
    ("cosa abbino a un prosciutto crudo?", "Sapidita"),

    # --- Casi lessicali: la domanda usa parole presenti letteralmente nella
    #     KB. Il semantico dovrebbe cavarsela, il lessicale anche.
    ("cos'e' la tendenza dolce di un cibo?", "Dolcezza"),
    ("come funziona l'abbinamento per contrapposizione?", "Principio"),
    ("cosa si intende per succulenza?", "Sapidita"),

    # --- Caso cross-culturale: e' la ragione dichiarata per cui esiste la
    #     componente lessicale. Se l'ibrido non batte il semantico QUI, non
    #     lo batte da nessuna parte.
    ("che vino abbino al ndole?", "ndole"),
    ("come si abbina un piatto africano?", "ndole"),
    ("vino per un curry indiano piccante", "amara"),
]

STRATEGIE = ["ibrida", "semantica", "lessicale"]
TOP_K = 3


def posizione_corretta(passaggi: list[str], atteso: str) -> int | None:
    """Posizione (1-based) del primo passaggio del documento atteso."""
    for i, p in enumerate(passaggi, 1):
        titolo = p.split("\n")[0]
        if atteso.lower() in titolo.lower():
            return i
    return None


def valuta(retriever: KnowledgeRetriever, strategia: str) -> dict:
    """Hit rate e MRR di una strategia di recupero sull'insieme di domande."""
    trovati = 0
    somma_reciproci = 0.0
    fallimenti = []

    for domanda, atteso in DOMANDE:
        passaggi = retriever.search(domanda, top_k=TOP_K, strategia=strategia)
        pos = posizione_corretta(passaggi, atteso)
        if pos is None:
            fallimenti.append(domanda)
        else:
            trovati += 1
            somma_reciproci += 1.0 / pos

    n = len(DOMANDE)
    return {
        "hit_rate": trovati / n,
        "mrr": somma_reciproci / n,
        "fallimenti": fallimenti,
    }


def main() -> None:
    """Valuta le tre strategie di recupero e stampa hit rate e MRR."""
    retriever = KnowledgeRetriever()

    print(f"Valutazione del retrieval su {len(DOMANDE)} domande, top_k={TOP_K}\n")
    print(f"{'strategia':<12} {'hit rate@3':>11} {'MRR':>7}")
    print("-" * 32)

    esiti = {}
    for s in STRATEGIE:
        r = valuta(retriever, s)
        esiti[s] = r
        print(f"{s:<12} {r['hit_rate']:>10.0%} {r['mrr']:>7.3f}")

    print("\nDomande fallite per strategia:")
    for s in STRATEGIE:
        f = esiti[s]["fallimenti"]
        print(f"\n  {s}:")
        if not f:
            print("    nessuna")
        for d in f:
            print(f"    - {d}")

    # Il confronto che giustifica (o smonta) la scelta architetturale.
    delta_hit = esiti["ibrida"]["hit_rate"] - esiti["semantica"]["hit_rate"]
    delta_mrr = esiti["ibrida"]["mrr"] - esiti["semantica"]["mrr"]
    print(
        f"\nIbrido meno semantico puro: "
        f"hit rate {delta_hit:+.0%}, MRR {delta_mrr:+.3f}"
    )
    if delta_hit <= 0 and delta_mrr <= 0:
        print(
            "La componente lessicale non porta guadagno su questo insieme di "
            "domande: andrebbe rimossa, oppure l'insieme e' troppo facile e "
            "va esteso ai casi in cui si presume che serva."
        )


if __name__ == "__main__":
    main()
