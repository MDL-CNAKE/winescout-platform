# Limiti del modello e sbilanciamento dei dati

## Distribuzione del target (qualità)

Il dataset Wine Quality (UCI) è fortemente sbilanciato sul punteggio di qualità:

| Qualità | N. vini | % sul totale |
|:---:|:---:|:---:|
| 3 | 30 | 0.5% |
| 4 | 216 | 3.3% |
| 5 | 2138 | 32.9% |
| 6 | 2836 | 43.7% |
| 7 | 1079 | 16.6% |
| 8 | 193 | 3.0% |
| 9 | 5 | 0.1% |

Le classi centrali 5 e 6 rappresentano da sole il **76.6%** dei campioni,
mentre gli estremi (vini scadenti o eccellenti) sono rari: la qualità 3 è lo
0.5% e la qualità 9 conta appena 5 vini su 6497.

## Impatto sul modello

Il problema affrontato è di **regressione** (predizione di un punteggio
continuo 3-9), non di classificazione. Per questo motivo il parametro
`class_weight` — citato dalla traccia come esempio di gestione dello
sbilanciamento — **non è applicabile**: è un parametro dei classificatori,
non dei regressori.

Lo sbilanciamento si riflette comunque sulle prestazioni: avendo pochissimi
esempi di vini eccellenti o scadenti, il modello tende a predire valori
vicini alla media (5-6), dove si concentra la quasi totalità dei dati.
Questo spiega perché l'R² si assesta intorno a 0.52: il modello coglie bene
la tendenza generale ma fatica sugli estremi, proprio quelli commercialmente
più interessanti (un vino eccellente o un difetto grave).

## Gestione adottata

Coerentemente con la natura del problema (regressione) e con la traccia
WineScout (che richiede esplicitamente un modello di regressione), lo
sbilanciamento è stato **riconosciuto e quantificato come limite noto**
anziché "corretto" con tecniche di classificazione non pertinenti.

Possibili sviluppi futuri per affrontarlo attivamente:
- pesare i campioni rari con `sample_weight` in fase di training;
- riformulare il problema come classificazione a 3 fasce
  (scarso / medio / ottimo) e usare `class_weight="balanced"`;
- raccogliere più dati sui vini agli estremi della scala qualitativa.

## Altri limiti noti

- **Bias geografico e tipologico**: il dataset contiene solo vini portoghesi
  fermi (rossi e bianchi Vinho Verde). Mancano rosati, spumanti, vini di
  altre regioni. Il modello non è affidabile fuori da questo dominio.
- **Dati commerciali simulati**: prezzo, margine, nome e abbinamento
  cibo-vino non provengono dal dataset originale (puramente chimico) ma sono
  generati con logiche esplicite e documentate (src/pricing.py, naming.py,
  pairing.py). Non sono dati reali di mercato.
- **Qualità come giudizio soggettivo**: il punteggio del dataset deriva da
  valutazioni sensoriali umane, intrinsecamente soggettive; nessun modello
  può replicarle con precisione perfetta.

## Bias culturale nel modello di embedding (sistema RAG)

### Il problema individuato

Durante lo sviluppo del sistema RAG per il Sommelier Virtuale abbiamo
testato il recupero semantico con domande su cucine diverse. Il test ha
rivelato un bias non previsto: il modello di embedding multilingue
(`paraphrase-multilingual-MiniLM-L12-v2`) **non rappresenta correttamente i
nomi di piatti extra-europei**.

Interrogando il sistema con "che vino abbino al ndolè?" (piatto tradizionale
camerunese), la ricerca puramente semantica **non recuperava** il documento
della knowledge base dedicato proprio al ndolè, mentre domande equivalenti su
piatti europei ("frittura di pesce", "dolce al cioccolato") recuperavano
correttamente i documenti pertinenti.

La causa e' che i modelli di embedding sono addestrati su corpora
prevalentemente occidentali: termini culinari non occidentali sono rari o
assenti nei dati di addestramento, quindi il modello non ne coglie il
significato.

### Perche' e' rilevante

Un sistema di raccomandazione enologica costruito ingenuamente su ricerca
semantica risulterebbe **sistematicamente meno utile per cucine non
occidentali**, pur senza alcuna intenzione discriminatoria da parte di chi lo
sviluppa. E' un esempio concreto di bias che si eredita dagli strumenti
utilizzati, non dai propri dati.

### Mitigazioni adottate

1. **Knowledge base costruita sulle sensazioni, non sui piatti.** I documenti
   descrivono dimensioni sensoriali universali (grassezza, sapidita, tendenza
   amara, piccantezza, dolcezza) invece di elencare ricette. Qualsiasi piatto
   del mondo puo essere abbinato scomponendolo nelle sue sensazioni, senza che
   il sistema debba "conoscerlo" come ricetta.

2. **Ricerca ibrida semantica + lessicale.** Al recupero per similarita
   semantica e' stato affiancato un match testuale letterale, che promuove i
   chunk contenenti esattamente i termini della domanda. Cosi nomi di piatti
   sconosciuti al modello vengono comunque trovati se presenti nella knowledge
   base (vedi `src/rag/retriever.py`).

3. **Esempio cross-culturale esplicito nella knowledge base.** Il documento
   `06_esempio_ndole_crossculturale.md` mostra la scomposizione sensoriale di
   un piatto non europeo, sia come riferimento per il retrieval sia come
   esempio di metodo per l'LLM.

### Limite residuo

Le mitigazioni riducono il problema ma non lo eliminano: per piatti non
presenti nella knowledge base e sconosciuti al modello, il sistema dipende
dalla capacita dell'LLM di scomporre correttamente il piatto nelle sue
sensazioni. Un'estensione futura sarebbe ampliare la knowledge base con
schede sensoriali di cucine diverse, redatte con il contributo di persone che
le conoscono direttamente.

## Assenza dell'informazione sul vitigno

Il dataset UCI Wine Quality (rossi e bianchi "Vinho Verde" portoghesi) non
include il vitigno (uva) di origine tra le sue colonne: contiene solo tipo
(rosso/bianco), 11 proprietà chimico-fisiche e un punteggio di qualità.

Per questo motivo il catalogo di WineScout non riporta e non inventa vitigni
per i singoli vini. I nomi mostrati nel catalogo sono descrittivi, derivati
dalla chimica (es. "Rosso Corposo Secco"), non nomi commerciali o varietali.

Il Sommelier Virtuale (LLM) è vincolato via prompt di sistema a non associare
mai un vitigno specifico a un vino del catalogo selezionato, per evitare di
presentare all'utente un'informazione plausibile ma non verificabile dai dati
di partenza. Il modello può discutere di vitigni solo in termini generali,
quando la domanda non riguarda un vino specifico del catalogo.
