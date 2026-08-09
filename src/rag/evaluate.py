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

DUE GROUND TRUTH, E PERCHE'
---------------------------
La prima valutazione mostro' tre domande che fallivano con ogni strategia
(carbonara, tiramisu, prosciutto crudo): la knowledge base descriveva
SENSAZIONI e chi domanda nomina PIATTI. La correzione e' stata aggiungere un
documento che scompone i piatti comuni nelle loro sensazioni.

A quel punto pero' si presenta una tentazione precisa: dichiarare che per
"carbonara" il documento atteso e' quello nuovo, e vedere il punteggio salire.
Sarebbe riscrivere il test perche' passi — la misura smetterebbe di misurare.

Percio' ogni domanda porta DUE riferimenti:

- ATTESO STRETTO: il documento dichiarato PRIMA di conoscere i risultati.
  Non e' mai stato modificato. E' il numero confrontabile con quello di ieri.
- ACCETTABILI: l'insieme dei documenti che rispondono davvero bene alla
  domanda. Per un piatto sono due — la scomposizione E la sensazione
  corrispondente — perche' l'LLM riceve k passaggi e li legge tutti.

Il punteggio ampio e' quello utile a giudicare il sistema; quello stretto e'
la garanzia che il miglioramento non venga dall'aver spostato il bersaglio.
Se salisse solo l'ampio, il documento nuovo starebbe rispondendo al posto di
quello sensoriale invece che insieme a lui — informazione da sapere, non da
nascondere.

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


# Ogni voce: (domanda, atteso_stretto, altri_accettabili).
#
# `atteso_stretto` e' il documento dichiarato PRIMA di vedere i risultati e
# non viene mai toccato: e' l'ancora che rende i numeri confrontabili nel
# tempo. `altri_accettabili` elenca i documenti che rispondono altrettanto
# bene, aggiunti quando la knowledge base cresce.
#
# Il confronto avviene sul titolo perche' e' prefisso di ogni chunk (vedi
# build_index.chunk_document): identifica il documento senza dipendere da
# come i paragrafi sono stati spezzati.
PIATTI = "Piatti comuni"

DOMANDE = [
    # --- Casi in cui le parole della domanda NON compaiono nella KB
    #     sensoriale: prima dell'aggiunta di 07_piatti_comuni_scomposti.md
    #     poteva funzionare solo la componente semantica.
    ("cosa bevo con una carbonara?", "Grassezza", [PIATTI]),
    ("che vino con una bistecca al sangue?", "Sapidita", [PIATTI]),
    ("abbinamento per un tiramisu", "Dolcezza", [PIATTI]),
    ("vino per un piatto molto speziato che brucia", "amara", [PIATTI]),
    ("che vino sta bene con il radicchio?", "amara", [PIATTI]),
    ("cosa abbino a un prosciutto crudo?", "Sapidita", [PIATTI]),

    # --- Casi lessicali: la domanda usa parole presenti letteralmente nella
    #     KB. Qui NON si allarga la ground truth: sono domande sul metodo, e
    #     la risposta giusta e' il documento sensoriale, non un elenco di
    #     piatti.
    ("cos'e' la tendenza dolce di un cibo?", "Dolcezza", []),
    ("come funziona l'abbinamento per contrapposizione?", "Principio", []),
    ("cosa si intende per succulenza?", "Sapidita", []),

    # --- Caso cross-culturale: e' la ragione dichiarata per cui esiste la
    #     componente lessicale. Se l'ibrido non batte il semantico QUI, non
    #     lo batte da nessuna parte.
    ("che vino abbino al ndole?", "ndole", []),
    ("come si abbina un piatto africano?", "ndole", []),
    ("vino per un curry indiano piccante", "amara", [PIATTI]),
]

STRATEGIE = ["ibrida", "semantica", "lessicale"]

# Scelto misurando, non a intuito: vedi la tabella stampata in fondo.
# Con 3 posti l'hit rate stretto era 67%, con 4 tornava a 75%, con 5 sale a
# 92% e con 6 non guadagna piu' nulla. I documenti sensoriali c'erano gia',
# stavano in quarta e quinta posizione — e' per questo che l'MRR migliora
# poco (0.542 -> 0.596) mentre l'hit rate migliora molto.
#
# AVVERTENZA. Questo valore e' stato scelto guardando LE STESSE 12 domande su
# cui viene poi misurato: il 92% e' quindi una stima ottimistica, non un
# risultato su dati mai visti. E' la versione in piccolo dello stesso errore
# trovato nel dataset del modello (vedi docs/model_limitations.md). Per una
# stima onesta servirebbe un secondo insieme di domande, tenuto da parte e
# mai consultato durante le scelte di progettazione.
TOP_K = 5


def posizione_corretta(passaggi: list[str], attesi: list[str]) -> int | None:
    """Posizione (1-based) del primo passaggio appartenente a un documento atteso."""
    for i, p in enumerate(passaggi, 1):
        titolo = p.split("\n")[0].lower()
        if any(a.lower() in titolo for a in attesi):
            return i
    return None


def valuta(retriever: KnowledgeRetriever, strategia: str, top_k: int = TOP_K) -> dict:
    """Hit rate e MRR di una strategia, in versione stretta e ampia.

    Il recupero viene eseguito UNA volta per domanda e valutato due volte con
    riferimenti diversi: cosi' i due punteggi descrivono lo stesso identico
    comportamento del sistema, non due esecuzioni che potrebbero divergere.
    """
    esiti = {
        "stretto": {"trovati": 0, "reciproci": 0.0, "fallimenti": []},
        "ampio": {"trovati": 0, "reciproci": 0.0, "fallimenti": []},
    }

    for domanda, stretto, altri in DOMANDE:
        passaggi = retriever.search(domanda, top_k=top_k, strategia=strategia)

        for chiave, attesi in (("stretto", [stretto]), ("ampio", [stretto] + altri)):
            pos = posizione_corretta(passaggi, attesi)
            if pos is None:
                esiti[chiave]["fallimenti"].append(domanda)
            else:
                esiti[chiave]["trovati"] += 1
                esiti[chiave]["reciproci"] += 1.0 / pos

    n = len(DOMANDE)
    return {
        chiave: {
            "hit_rate": e["trovati"] / n,
            "mrr": e["reciproci"] / n,
            "fallimenti": e["fallimenti"],
        }
        for chiave, e in esiti.items()
    }


# Riferimento storico: valutazione del 9 agosto 2026, PRIMA dell'aggiunta del
# documento sui piatti comuni. Serve a rendere il confronto immediato invece
# che affidato alla memoria di chi esegue lo script.
BASELINE = {"ibrida": 0.75, "lessicale": 0.58, "semantica": 0.42}


def main() -> None:
    """Valuta le tre strategie di recupero e stampa hit rate e MRR."""
    retriever = KnowledgeRetriever()

    print(f"Valutazione del retrieval su {len(DOMANDE)} domande, top_k={TOP_K}")
    print("stretto = ground truth originale, mai modificata")
    print("ampio   = include i documenti aggiunti dopo, altrettanto pertinenti\n")

    print(f"{'strategia':<12} {f'hit@{TOP_K} str':>10} {'MRR str':>8} "
          f"{f'hit@{TOP_K} amp':>10} {'MRR amp':>8} {'era':>6}")
    print("-" * 60)

    esiti = {}
    for s in STRATEGIE:
        r = valuta(retriever, s)
        esiti[s] = r
        print(f"{s:<12} {r['stretto']['hit_rate']:>9.0%} {r['stretto']['mrr']:>8.3f} "
              f"{r['ampio']['hit_rate']:>9.0%} {r['ampio']['mrr']:>8.3f} "
              f"{BASELINE[s]:>5.0%}")

    print("\nDomande ancora fallite (criterio ampio):")
    for s in STRATEGIE:
        f = esiti[s]["ampio"]["fallimenti"]
        print(f"\n  {s}:")
        if not f:
            print("    nessuna")
        for d in f:
            print(f"    - {d}")

    # Diagnostica sui fallimenti STRETTI della strategia in produzione.
    # Serve a smettere di formulare ipotesi sul perche' una domanda sbagli:
    # si guarda cosa e' stato effettivamente recuperato e al posto di cosa.
    print("\n" + "-" * 60)
    print("COSA VIENE RECUPERATO dove il documento sensoriale non arriva")
    print("-" * 60)
    for domanda, stretto, _ in DOMANDE:
        if domanda not in esiti["ibrida"]["stretto"]["fallimenti"]:
            continue
        passaggi = retriever.search(domanda, top_k=TOP_K, strategia="ibrida")
        print(f"\n  {domanda}")
        print(f"    atteso: {stretto}")
        for i, p in enumerate(passaggi, 1):
            print(f"    {i}. {p.split(chr(10))[0][:62]}")

    # Il confronto che giustifica (o smonta) la scelta architetturale.
    ib, se = esiti["ibrida"]["ampio"], esiti["semantica"]["ampio"]
    delta_hit = ib["hit_rate"] - se["hit_rate"]
    delta_mrr = ib["mrr"] - se["mrr"]
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

    # Quanti passaggi servono davvero?
    #
    # top_k non e' una costante di comodo: e' un compromesso fra copertura e
    # costo. Ogni passaggio in piu' entra nel prompt e si paga a ogni domanda,
    # ma con sette documenti tematici tre posti potrebbero non bastare piu'.
    # Il numero giusto si misura, non si sceglie.
    print("\n" + "-" * 60)
    print("QUANTI PASSAGGI SERVONO (strategia ibrida)")
    print("-" * 60)
    print(f"{'top_k':>6} {'hit str':>9} {'MRR str':>9} {'hit amp':>9} {'MRR amp':>9}")

    for k in (3, 4, 5, 6):
        r = valuta(retriever, "ibrida", top_k=k)
        print(f"{k:>6} {r['stretto']['hit_rate']:>8.0%} {r['stretto']['mrr']:>9.3f} "
              f"{r['ampio']['hit_rate']:>8.0%} {r['ampio']['mrr']:>9.3f}")

    print()
    print("MRR non cambia allargando k: misura la POSIZIONE del primo")
    print("documento corretto, che non si sposta se si aggiungono posti in")
    print("fondo. Se sale l'hit rate ma non l'MRR, il documento giusto e'")
    print("stato recuperato ma sta in coda, dietro a passaggi meno pertinenti.")

    # Il controllo che smaschera l'autoinganno.
    stretto = esiti["ibrida"]["stretto"]["hit_rate"]
    ampio = esiti["ibrida"]["ampio"]["hit_rate"]
    print()
    print("=" * 60)
    if stretto < BASELINE["ibrida"] and ampio > BASELINE["ibrida"]:
        print("ATTENZIONE: il punteggio sale solo col criterio ampio, e quello")
        print("stretto SCENDE. Il documento nuovo sta prendendo il posto di")
        print("quello sensoriale invece di affiancarlo: l'LLM riceve la")
        print("scomposizione del piatto ma non la regola di abbinamento.")
        print("Il miglioramento e' apparente.")
    elif ampio > BASELINE["ibrida"]:
        print("Il documento nuovo affianca quello sensoriale senza sostituirlo:")
        print("il miglioramento e' reale.")
    else:
        print("Nessun miglioramento rispetto alla baseline.")
    print("=" * 60)


if __name__ == "__main__":
    main()
