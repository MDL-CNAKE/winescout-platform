"""Bilancia e prepara alla revisione le domande generate.

DUE PROBLEMI EMERSI DALLA PRIMA GENERAZIONE
-------------------------------------------
1. SQUILIBRIO. Il 61% delle domande aveva come risposta attesa un solo
   documento, quello sui piatti comuni, mentre "Tendenza amara" ne aveva due.
   La causa e' meccanica: quel documento e' piu' lungo, produce piu' chunk, e
   si generano due domande per chunk. L'insieme di valutazione ha ereditato la
   STRUTTURA della knowledge base invece di rispecchiare le domande che la
   gente fa davvero. Un insieme cosi' misura soprattutto quanto bene si
   recupera il documento piu' lungo.

2. GROUND TRUTH SPESSO SBAGLIATA. Il presupposto della generazione automatica
   e': "il chunk che ha ispirato la domanda e' anche quello che la risponde
   meglio". E' falso. Esempi reali dalla prima esecuzione:

     "Che vino scelgo per un tagliere di salumi molto unti?"
        atteso: Principio fondamentale   -> corretto: Grassezza e untuosita
     "Meglio un vino secco o uno dolce per il dessert?"
        atteso: Principio fondamentale   -> corretto: Dolcezza

   Il modello scrive domande ISPIRATE al testo, non domande a cui quel testo
   e' la risposta migliore. E' il limite di fondo della ground truth
   sintetica, e nessuna misura costruita su di essa vale niente finche' non
   viene corretta a mano.

COSA FA QUESTO SCRIPT
---------------------
Non decide al posto di chi rivede: prepara il lavoro.

- Bilancia, tenendo al massimo N domande per documento. Fra quelle in eccesso
  scarta prima le piu' vicine lessicalmente al testo d'origine, cioe' le piu'
  simili a una parafrasi e le meno simili a una domanda vera.
- Non cancella nulla: marca "scartata": true con il motivo, cosi' resta
  scritto perche' un caso e' uscito dall'insieme.
- Stampa le domande rimaste raggruppate per documento atteso, in una forma
  comoda da leggere e correggere.

Uso:
    python src/rag/rivedi_domande.py --max-per-documento 8
    python src/rag/rivedi_domande.py --solo-elenco
"""
import argparse
import collections
import json
import os
import sys
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

FILE = Path("docs/rag_eval/domande.json")


def carica() -> list[dict]:
    """Legge il file delle domande generate."""
    if not FILE.exists():
        sys.exit(f"{FILE} non esiste: esegui prima src/rag/genera_domande.py")
    return json.loads(FILE.read_text(encoding="utf-8"))


def bilancia(voci: list[dict], massimo: int) -> int:
    """Tiene al massimo `massimo` domande per documento atteso.

    Il criterio di scarto e' la sovrapposizione lessicale col testo
    d'origine, dalla piu' alta alla piu' bassa: si eliminano per prime le
    domande che riusano le parole del documento, perche' sono le meno simili
    a cio' che scriverebbe una persona e le piu' facili da recuperare per la
    componente lessicale. Scartare a caso butterebbe via anche domande buone.
    """
    per_documento = collections.defaultdict(list)
    for v in voci:
        if not v.get("scartata"):
            per_documento[v["documento_atteso"]].append(v)

    scartate = 0
    for _, gruppo in per_documento.items():
        if len(gruppo) <= massimo:
            continue
        # Piu' sovrapposizione = piu' parafrasi = si scarta prima.
        gruppo.sort(key=lambda v: (-v["sovrapposizione"], v["domanda"]))
        for v in gruppo[: len(gruppo) - massimo]:
            v["scartata"] = True
            v["motivo"] = "bilanciamento: documento sovrarappresentato"
            scartate += 1

    return scartate


def stampa_per_revisione(voci: list[dict]) -> None:
    """Elenco leggibile, raggruppato per documento atteso.

    Il formato serve a rispondere a una domanda sola, per ciascuna riga:
    "se questa fosse la domanda di un cliente, il documento indicato sarebbe
    davvero quello da recuperare?".
    """
    attive = [v for v in voci if not v.get("scartata")]
    per_documento = collections.defaultdict(list)
    for v in attive:
        per_documento[v["documento_atteso"]].append(v)

    for doc in sorted(per_documento):
        gruppo = per_documento[doc]
        print(f"\n{'=' * 66}")
        print(f"{doc}  ({len(gruppo)} domande)")
        print("=" * 66)
        for v in gruppo:
            marca = "V" if v["insieme"] == "verifica" else "s"
            print(f"  [{marca}] {v['domanda']}")


def main() -> None:
    """Bilancia le domande e le stampa per la revisione a mano."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-per-documento", type=int, default=8)
    parser.add_argument("--solo-elenco", action="store_true",
                        help="stampa senza modificare il file")
    args = parser.parse_args()

    voci = carica()
    prima = len([v for v in voci if not v.get("scartata")])

    if not args.solo_elenco:
        scartate = bilancia(voci, args.max_per_documento)
        FILE.write_text(json.dumps(voci, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Bilanciamento: {scartate} domande marcate come scartate "
              f"(max {args.max_per_documento} per documento)")

    attive = [v for v in voci if not v.get("scartata")]
    sviluppo = [v for v in attive if v["insieme"] == "sviluppo"]
    verifica = [v for v in attive if v["insieme"] == "verifica"]

    print(f"\nDomande attive: {len(attive)} (erano {prima})")
    print(f"  sviluppo: {len(sviluppo)}")
    print(f"  verifica: {len(verifica)}")

    conteggi = collections.Counter(v["documento_atteso"] for v in attive)
    print("\nDistribuzione per documento atteso:")
    for doc, n in conteggi.most_common():
        print(f"  {n:3d}  {doc[:56]}")

    stampa_per_revisione(voci)

    print(f"\n{'=' * 66}")
    print("ORA LA PARTE CHE NESSUNO SCRIPT PUO' FARE")
    print("=" * 66)
    print("Per ogni riga, chiediti: se un cliente scrivesse questa domanda, il")
    print("documento sotto cui e' elencata sarebbe davvero quello da")
    print("recuperare? Se no, correggi 'documento_atteso' nel JSON. Se la")
    print("domanda e' troppo vaga perche' un documento sia piu' giusto di un")
    print("altro, marcala scartata con il motivo.")
    print()
    print("La ground truth automatica fa risparmiare la scrittura delle")
    print("domande, non il giudizio su quale sia la risposta giusta.")


if __name__ == "__main__":
    main()
