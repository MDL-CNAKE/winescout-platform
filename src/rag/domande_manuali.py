"""Domande scritte a mano per i documenti che il generatore non copre.

PERCHE' SERVONO
---------------
Dopo generazione, bilanciamento e revisione, due documenti restavano quasi
scoperti: "Principio fondamentale dell'abbinamento cibo-vino" con una sola
domanda e "Tendenza amara e piccantezza" con tre.

Non e' sfortuna, e' una proprieta' del metodo. Il generatore legge un
passaggio e scrive domande che quel passaggio SUGGERISCE; davanti a un testo
sul metodo continua a scrivere domande su piatti concreti, perche' e' cosi'
che parlano le persone. Il risultato e' che i documenti teorici restano senza
domande proprie.

E' il limite generale della generazione sintetica a partire dai documenti:
produce le domande che il corpus suggerisce, non quelle che al corpus
mancano. Per quelle serve qualcuno che guardi la distribuzione e scriva cio'
che non c'e'.

CRITERIO DI SCRITTURA
---------------------
Le domande sul metodo non sono astratte: sono quelle che una persona fa
quando non ha in mente un piatto ma un dubbio ("il vino deve assomigliare al
cibo o contrastarlo?"). Restano nel registro di chi chiede, senza usare i
termini tecnici del documento — la stessa regola imposta al generatore, per
non rendere queste domande piu' facili delle altre.

Uso: python src/rag/domande_manuali.py
"""
import hashlib
import json
import os
import re
import sys
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.rag.genera_domande import insieme_di, sovrapposizione_lessicale
from src.rag.build_index import KB_DIR, chunk_document

FILE = Path("docs/rag_eval/domande.json")

PRINCIPIO = "Principio fondamentale dell'abbinamento cibo-vino"
AMARA = "Tendenza amara e piccantezza del cibo"

# Domande sul METODO: chi le scrive non ha in mente un piatto ma un dubbio.
# Sono quelle che il generatore non produce mai.
DOMANDE = [
    (PRINCIPIO, "Il vino deve assomigliare al piatto o fare da contrasto?"),
    (PRINCIPIO, "Esiste una regola generale per non sbagliare l'abbinamento?"),
    (PRINCIPIO, "Come faccio a capire se un vino sta bene con quello che ho cucinato?"),
    (PRINCIPIO, "Conta piu' il tipo di carne o come e' cucinata?"),
    (PRINCIPIO, "Perche' certi abbinamenti che sembrano sensati poi non funzionano?"),

    (AMARA, "Che vino prendo per un piatto che pizzica parecchio?"),
    (AMARA, "Con le verdure amare come la cicoria cosa si beve?"),
    (AMARA, "Il vino rosso peggiora il bruciore dei piatti piccanti?"),
    (AMARA, "Che vino metto in tavola con una cena a base di radicchio e carciofi?"),
]


def testo_documento(titolo: str) -> str:
    """Testo completo del documento, per calcolare la sovrapposizione."""
    for path in sorted(KB_DIR.glob("*.md")):
        contenuto = path.read_text(encoding="utf-8")
        if contenuto.split("\n")[0].lstrip("# ").strip() == titolo:
            return contenuto
    return ""


def main() -> None:
    """Aggiunge le domande manuali al file, senza toccare quelle esistenti."""
    if not FILE.exists():
        sys.exit(f"{FILE} non esiste: esegui prima src/rag/genera_domande.py")

    voci = json.loads(FILE.read_text(encoding="utf-8"))
    esistenti = {v["domanda"].lower().strip("?. ") for v in voci}

    aggiunte = 0
    for documento, domanda in DOMANDE:
        if domanda.lower().strip("?. ") in esistenti:
            continue
        voci.append({
            "domanda": domanda,
            "documento_atteso": documento,
            # Stessa funzione di divisione delle domande generate: e'
            # l'unico modo perche' i due insiemi restino confrontabili.
            "insieme": insieme_di(domanda),
            "sovrapposizione": round(
                sovrapposizione_lessicale(domanda, testo_documento(documento)), 2
            ),
            "scartata": False,
            "origine": "manuale",
        })
        aggiunte += 1

    FILE.write_text(json.dumps(voci, ensure_ascii=False, indent=2), encoding="utf-8")

    import collections
    attive = [v for v in voci if not v.get("scartata")]
    conteggi = collections.Counter(v["documento_atteso"] for v in attive)
    manuali = [v for v in attive if v.get("origine") == "manuale"]

    print(f"Aggiunte {aggiunte} domande manuali")
    print(f"Insieme attivo: {len(attive)} domande "
          f"({len(manuali)} manuali, {len(attive) - len(manuali)} generate)")

    print("\nDistribuzione per documento atteso:")
    for doc, n in conteggi.most_common():
        print(f"  {n:3d}  {doc[:56]}")

    sviluppo = [v for v in attive if v["insieme"] == "sviluppo"]
    verifica = [v for v in attive if v["insieme"] == "verifica"]
    print(f"\nsviluppo: {len(sviluppo)}   verifica: {len(verifica)}")

    media_gen = [v["sovrapposizione"] for v in attive if v.get("origine") != "manuale"]
    media_man = [v["sovrapposizione"] for v in manuali]
    if media_gen and media_man:
        print(f"\nSovrapposizione lessicale media:")
        print(f"  domande generate: {sum(media_gen)/len(media_gen):.2f}")
        print(f"  domande manuali:  {sum(media_man)/len(media_man):.2f}")
        print("Se quelle manuali fossero molto piu' basse, sarebbero piu'")
        print("difficili delle altre e il confronto fra documenti ne")
        print("risentirebbe: e' un controllo, non una formalita'.")


if __name__ == "__main__":
    main()
