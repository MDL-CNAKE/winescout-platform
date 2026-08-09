"""Genera un insieme di domande per valutare il retrieval.

PERCHE'
-------
Le prime valutazioni sono state fatte su 12 domande scritte a mano. Con 12
domande una sola risposta sbagliata vale 8 punti percentuali: si e' discusso
di uno scarto fra 67% e 75% che era, letteralmente, UNA domanda. Nessuna delle
decisioni prese su quei numeri era statisticamente sostenuta.

COME FUNZIONA
-------------
Per ogni passaggio della knowledge base si chiede al modello: "quale domanda
farebbe un vignaiolo, se questo testo fosse la risposta?". La ground truth e'
automatica — e' il documento da cui la domanda e' nata — e questo e' l'unico
motivo per cui si possono generare decine di domande senza etichettarle a
mano una per una.

E' la tecnica standard per costruire un insieme di valutazione sintetico per
un sistema RAG.

IL RISCHIO, DICHIARATO E MISURATO
---------------------------------
Una domanda generata a partire da un testo tende a RIUSARE LE PAROLE di quel
testo. Il retrieval ibrido di questo progetto si regge anche sulla
corrispondenza lessicale: un insieme di domande cosi' costruito la
avvantaggerebbe artificialmente, e concluderemmo che la componente lessicale
funziona meglio di quanto faccia sulle domande vere.

Due contromisure:
1. Il prompt chiede esplicitamente di scrivere come parlerebbe un cliente,
   senza riusare i termini tecnici del passaggio.
2. Lo script MISURA la sovrapposizione lessicale fra ogni domanda e il testo
   da cui nasce, e la riporta. Se resta alta, la contromisura non ha
   funzionato e i numeri vanno letti sapendolo.

DUE INSIEMI
-----------
Le domande vengono divise in SVILUPPO (per tarare parametri come top_k) e
VERIFICA (consultato solo per dichiarare i risultati finali). E' la stessa
logica del test set nel machine learning, ed e' la correzione del difetto
documentato in docs/model_limitations.md: top_k era stato scelto guardando le
stesse domande su cui veniva poi misurato.

La divisione e' DETERMINISTICA, calcolata dall'hash del testo della domanda e
non da un mescolamento casuale: cosi' aggiungere domande in futuro non sposta
quelle esistenti da un insieme all'altro, che invaliderebbe ogni confronto
storico.

REVISIONE A MANO
----------------
L'output e' un JSON pensato per essere letto e corretto. Una domanda si
esclude aggiungendole "scartata": true, senza cancellarla: resta la traccia
del perche' un certo caso non e' stato considerato valido.

Uso: python src/rag/genera_domande.py [--per-chunk 2]
"""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import requests

from src.rag.build_index import KB_DIR, chunk_document

USCITA = Path("docs/rag_eval/domande.json")

# Frazione destinata alla verifica. Un terzo e' un compromesso: abbastanza da
# dare un numero credibile, non tanto da lasciare troppo poche domande per
# tarare i parametri.
QUOTA_VERIFICA = 0.33

PROMPT = (
    "Sei un vignaiolo o un cliente di una piccola cantina, non un enologo.\n\n"
    "Ti viene mostrato un passaggio di un manuale di abbinamento cibo-vino. "
    "Scrivi {n} domande DIVERSE che avrebbero questo passaggio come risposta "
    "utile.\n\n"
    "REGOLE INDEROGABILI.\n"
    "1. NON riusare i termini tecnici del passaggio (grassezza, sapidita', "
    "succulenza, tendenza amara, contrapposizione, concordanza). Scrivi come "
    "parla una persona normale: nomina piatti, situazioni, dubbi concreti.\n"
    "2. Ogni domanda deve reggersi da sola, senza riferimenti a 'questo testo' "
    "o 'il passaggio'.\n"
    "3. Domande brevi, come si scrivono davvero in una casella di ricerca.\n"
    "4. Variale: alcune su un piatto specifico, alcune su una situazione "
    "(una cena, un regalo), alcune su un dubbio pratico.\n\n"
    "Rispondi SOLO con una lista JSON di stringhe, niente altro."
)


def leggi_chunk() -> list[tuple[str, str]]:
    """Restituisce (titolo_documento, testo_chunk) per tutta la knowledge base.

    Usa la STESSA funzione di chunking dell'indice: se i chunk qui fossero
    diversi da quelli indicizzati, la ground truth punterebbe a passaggi che
    il retriever non puo' restituire.
    """
    coppie = []
    for path in sorted(KB_DIR.glob("*.md")):
        testo = path.read_text(encoding="utf-8")
        titolo = testo.split("\n")[0].lstrip("# ").strip()
        for chunk in chunk_document(testo, titolo):
            coppie.append((titolo, chunk))
    return coppie


def genera_per_chunk(chunk: str, n: int, api_key: str, model: str) -> list[str]:
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "max_tokens": 400,
            # Temperatura alta di proposito: qui serve VARIETA'. Domande tutte
            # uguali gonfierebbero il conteggio senza aggiungere copertura.
            "temperature": 0.9,
            "messages": [
                {"role": "system", "content": PROMPT.format(n=n)},
                {"role": "user", "content": chunk},
            ],
        },
        timeout=60,
    )
    r.raise_for_status()
    grezzo = r.json()["choices"][0]["message"]["content"]

    inizio, fine = grezzo.find("["), grezzo.rfind("]")
    if inizio == -1 or fine == -1:
        return []
    try:
        domande = json.loads(grezzo[inizio:fine + 1])
    except json.JSONDecodeError:
        return []
    return [d.strip() for d in domande if isinstance(d, str) and d.strip()]


_PAROLA = re.compile(r"[a-zàèéìòùáíóú]{4,}", re.IGNORECASE)


def sovrapposizione_lessicale(domanda: str, chunk: str) -> float:
    """Quanta parte delle parole della domanda compare gia' nel passaggio.

    E' la misura del rischio dichiarato in testa al file. Un valore alto
    significa che la domanda e' una parafrasi del testo, e che il retrieval
    lessicale la trovera' con troppa facilita' rispetto a una domanda vera.
    """
    parole_domanda = {p.lower() for p in _PAROLA.findall(domanda)}
    if not parole_domanda:
        return 0.0
    parole_chunk = {p.lower() for p in _PAROLA.findall(chunk)}
    return len(parole_domanda & parole_chunk) / len(parole_domanda)


def insieme_di(domanda: str) -> str:
    """Sviluppo o verifica, deciso dall'hash del testo.

    Deterministico apposta: aggiungere domande in futuro non deve spostare
    quelle esistenti fra i due insiemi, altrimenti nessun confronto con le
    misure precedenti resterebbe valido.
    """
    digest = hashlib.sha256(domanda.encode("utf-8")).hexdigest()
    return "verifica" if int(digest[:8], 16) / 0xFFFFFFFF < QUOTA_VERIFICA else "sviluppo"


def main() -> None:
    """Genera le domande e le salva in docs/rag_eval/domande.json."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-chunk", type=int, default=2,
                        help="quante domande generare per ogni passaggio")
    args = parser.parse_args()

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv("LLM_MODEL", "meta-llama/llama-3.1-8b-instruct")
    if not api_key or api_key == "metti_qui_la_tua_chiave":
        sys.exit("Serve OPENROUTER_API_KEY per generare le domande.")

    chunk = leggi_chunk()
    print(f"Knowledge base: {len(chunk)} passaggi\n")

    voci = []
    visti: set[str] = set()

    for i, (titolo, testo) in enumerate(chunk, 1):
        print(f"  [{i}/{len(chunk)}] {titolo[:50]}...", flush=True)
        for domanda in genera_per_chunk(testo, args.per_chunk, api_key, model):
            chiave = domanda.lower().strip("?. ")
            if chiave in visti:      # il modello ripete, fra un chunk e l'altro
                continue
            visti.add(chiave)
            voci.append({
                "domanda": domanda,
                "documento_atteso": titolo,
                "insieme": insieme_di(domanda),
                "sovrapposizione": round(sovrapposizione_lessicale(domanda, testo), 2),
                "scartata": False,
            })

    USCITA.parent.mkdir(parents=True, exist_ok=True)
    USCITA.write_text(
        json.dumps(voci, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    sviluppo = [v for v in voci if v["insieme"] == "sviluppo"]
    verifica = [v for v in voci if v["insieme"] == "verifica"]
    media = sum(v["sovrapposizione"] for v in voci) / len(voci) if voci else 0
    alte = [v for v in voci if v["sovrapposizione"] > 0.5]

    print(f"\n{len(voci)} domande salvate in {USCITA}")
    print(f"  sviluppo: {len(sviluppo)}")
    print(f"  verifica: {len(verifica)}")
    print(f"\nSovrapposizione lessicale media con il testo d'origine: {media:.2f}")
    print(f"Domande sopra 0.50 (parafrasi del passaggio): {len(alte)}")
    if media > 0.4:
        print("\nATTENZIONE: sovrapposizione alta. Le domande riusano il")
        print("vocabolario dei documenti, quindi il recupero lessicale risultera'")
        print("migliore di quanto sia davvero. Vanno riscritte o scartate a mano.")
    print("\nProssimo passo: rileggere il file e marcare 'scartata': true le")
    print("domande implausibili o mal etichettate. La revisione umana non e'")
    print("opzionale: la ground truth automatica e' comoda, non affidabile.")


if __name__ == "__main__":
    main()
