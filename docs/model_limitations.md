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

## Granularità insufficiente delle regole di abbinamento

### Il problema individuato

Sfogliando il catalogo emerge che decine di vini consecutivi propongono lo
stesso identico abbinamento ("Tagliatelle al ragù, tagliere di salumi, pollo
arrosto, pecorino semi-stagionato"). Non è un errore di implementazione ma
un limite strutturale, dovuto a due cause che si sommano:

1. **Poche fasce, molti vini.** `src/pairing.py` classifica 6497 vini in
   sole 7 fasce (dolce, amabile, rosso corposo, rosso leggero, bianco acido,
   bianco corposo, bianco leggero). In media oltre 900 vini condividono la
   stessa stringa: la ripetizione è matematicamente inevitabile.
2. **Ordinamento sequenziale del dataset.** Il CSV UCI elenca prima tutti i
   rossi e poi tutti i bianchi, e all'interno di ciascun blocco i campioni
   sono spesso raggruppati per lotti analitici con profili chimici simili. I
   primi record del catalogo cadono quindi quasi tutti nella stessa fascia,
   rendendo la ripetizione immediatamente visibile.

### Perché è rilevante

Un sistema a regole con poche classi produce output *corretti* ma poco
*informativi*: se l'abbinamento è identico per un vino su sette, smette di
essere un consiglio e diventa rumore. È il limite tipico dei sistemi
rule-based rispetto a un modello appreso dai dati — con il vantaggio, però,
di essere ispezionabile e giustificabile riga per riga, cosa che una
raccomandazione appresa non offrirebbe.

### Mitigazioni adottate

1. **Rotazione del piatto mostrato.** Ogni fascia contiene già 4 piatti
   diversi: nelle card il piatto visualizzato viene scelto in modo
   deterministico a partire dall'id del vino, così referenze adiacenti non
   ripetono la stessa dicitura. La scheda completa resta visibile nella
   pagina del vino.
2. **Ordine del catalogo non sequenziale.** Il catalogo non rispetta più
   l'ordine di inserimento del CSV, che accorpava vini simili: l'utente vede
   affiancate tipologie diverse.

### Limite residuo

Le mitigazioni agiscono sulla *presentazione*, non sulla granularità delle
regole: due vini della stessa fascia restano indistinguibili sul piano
dell'abbinamento. Un'estensione futura sarebbe introdurre sotto-regole basate
su parametri finora inutilizzati (pH, acidità volatile, solfati) per
distinguere, ad esempio, un rosso leggero molto acido — adatto a piatti più
grassi — da uno più morbido. Questo richiede rigenerare la migrazione V5.

## Soglie di dolcezza arbitrarie nei descrittori (corretto)

### Il problema individuato

La prima versione di `src/naming.py` classificava la dolcezza con soglie
scelte a intuito — secco ≤ 2 g/L, dolce ≥ 10 g/L — e combinava liberamente
il descrittore di corpo con quello di dolcezza. Il risultato erano nomi come
**"Bianco Corposo Dolce"**, prodotti 39 volte, che non appartengono al
lessico enologico: "corposo" è vocabolario da vino secco, mentre per un
passito o un muffato si parla di concentrazione, non di corpo.

Il difetto vero non era la combinazione, era la soglia: con 10 g/L come
limite del "dolce", venivano etichettati come dolci 1222 vini che dolci non
sono.

### La correzione

Le soglie ora seguono il **Regolamento (UE) 2019/33, Allegato III**, che
classifica i vini fermi per zucchero residuo prevedendo una correzione per
l'acidità — a parità di zucchero, un vino più acido è percepito più secco:

    secco      ≤ 4 g/L, oppure ≤ 9 g/L se acidità ≥ zucchero − 2
    abboccato  ≤ 12 g/L, oppure ≤ 18 g/L se acidità ≥ zucchero − 10
    amabile    12 – 45 g/L
    dolce      > 45 g/L

Applicate al dataset, la distribuzione cambia radicalmente:

| Categoria | N. vini | % |
|---|---:|---:|
| secco | 5047 | 77,7% |
| abboccato | 1285 | 19,8% |
| amabile | 164 | 2,5% |
| dolce | 1 | 0,02% |

Un solo vino su 6497 è realmente dolce (65,8 g/L). Gli incroci problematici
scompaiono: "corposo + dolce" passa da 39 casi a **zero**.

Le soglie vivono ora in `src/wine_style.py`, condiviso da `naming.py` e
`pairing.py`: un vino non può più essere chiamato "Abboccato" dal generatore
di nomi e abbinato come passito da quello degli abbinamenti.

### Effetto collaterale gestito

Con le soglie corrette il 78% del catalogo risulta secco: esplicitarlo nel
nome avrebbe reso metà dei vini omonimi ("Rosso Equilibrato Secco") senza
aggiungere informazione. Si è quindi adottato il registro enologico reale,
dove **"secco" è la condizione implicita e non si menziona** (nessuno chiama
un Chianti "Chianti secco"): si nomina solo l'eccezione. I vini secchi
portano al suo posto un descrittore di freschezza derivato dal pH — fresco
(≤ 3,15), armonico, morbido (≥ 3,40) — che usa una colonna del dataset fino
ad allora inutilizzata nel naming.

### Limite residuo

Il dataset riporta `fixed_acidity` (acido tartarico in g/dm³), mentre la
norma UE fa riferimento all'**acidità totale**. L'acidità fissa ne è la
componente prevalente ma non coincide: la correzione per l'acidità è quindi
applicata su un proxy, e in una manciata di casi al confine fra due
categorie potrebbe assegnare la classe adiacente. La scelta è dichiarata
perché il dato esatto non è ricavabile dal dataset.

## "Riserva" usata come sinonimo di qualità alta (corretto)

### Il problema individuato

`src/naming.py` aggiungeva la menzione **Riserva** a ogni vino con punteggio
di qualità ≥ 7, cioè a circa il 20% del catalogo. Sfogliando la griglia
ordinata per qualità decrescente il difetto saltava all'occhio: pagine
intere di bianchi "Riserva".

Nel diritto vitivinicolo italiano *Riserva* non è un giudizio qualitativo:
è una **menzione tradizionale che indica un periodo minimo di affinamento**,
fissato dal disciplinare di ciascuna DOC o DOCG. Il dataset UCI non contiene
né la durata dell'affinamento, né l'annata, né la denominazione — quindi la
menzione veniva attribuita sulla base di un dato che non ha nulla a che
vedere con ciò che quella parola significa. Sui bianchi l'incongruenza è
ancora più marcata, perché diversi disciplinari per i bianchi la Riserva non
la prevedono affatto.

È lo stesso schema di errore delle soglie di dolcezza arbitrarie: prendere
un termine tecnico del lessico enologico e usarlo per dire un'altra cosa.

### La correzione

La menzione è stata **rimossa dai nomi**. La qualità resta pienamente
visibile nell'interfaccia come punteggio (★ 7/10), dove è leggibile senza
travestirsi da categoria merceologica normata.

I criteri che dipendevano dalla menzione sono stati riportati al dato che
realmente li motivava:

- lo stile di packaging "Elegante" si basa ora sul punteggio (≥ 7) invece
  che sulla presenza della parola nel nome;
- il formato Magnum sui punteggi ≥ 8;
- la veste austera della bottiglia generata (capsula scura allungata,
  filetti oro, colore più concentrato) sui punteggi ≥ 8.

La regola generale che se ne ricava, applicata in tutto il progetto: un
termine enologico normato si usa solo se il dato che lo giustifica è
presente nel dataset. Vale per il vitigno, per la dolcezza e ora per la
menzione Riserva.

## Indice di conservazione: cosa misura e cosa no

### Perché non si chiama "potenziale di invecchiamento"

L'indice implementato in `src/conservation.py` valuta la **predisposizione
alla conservazione**: la capacità del vino di resistere a ossidazione e
alterazione microbica. Non valuta il potenziale di invecchiamento nobile,
cioè l'evoluzione verso i profumi terziari e l'assestamento della struttura.

La distinzione non è terminologica ma sostanziale. L'invecchiamento dipende
in larga parte da **tannini, polifenoli ed estratto secco**, che nel dataset
UCI non compaiono. Per un vino rosso il tannino è la struttura portante
dell'invecchiamento: senza quel dato, qualunque previsione sull'evoluzione
sarebbe inventata. Il nome dichiara quindi ciò che l'indice misura davvero.

### Non è un modello addestrato

Il dataset non contiene alcuna etichetta sull'evoluzione dei vini nel tempo:
non esiste una verità di riferimento su cui addestrare o validare. L'indice è
perciò un **sistema a regole** costruito su parametri enologici consolidati,
come `src/pairing.py`. Non ha un'accuratezza misurabile: ha una motivazione
ispezionabile riga per riga. Presentarlo come machine learning sarebbe una
falsificazione.

### Su cosa si basa

| Indicatore | Peso | Motivazione |
|---|---:|---|
| SO₂ molecolare | 40% | Frazione di solforosa realmente attiva, calcolata da SO₂ libera e pH secondo la formula standard `SO₂lib / (1 + 10^(pH − 1,81))`. Riferimento operativo 0,5–0,8 mg/L. È l'unico parametro su cui la cantina può intervenire direttamente |
| Acidità volatile | 30% | Marcatore di deterioramento già in atto, confrontato con i limiti di legge UE (1,2 g/L rossi, 1,08 g/L bianchi) |
| pH | 20% | Conservante di per sé, e governa l'efficacia della solforosa |
| Quota di SO₂ libera sul totale | 10% | Indica quanta riserva protettiva è ancora disponibile e non legata |

### Verifica di non ridondanza

Sul catalogo, la correlazione fra indice di conservazione e punteggio di
qualità è **0,163**: praticamente nulla. L'indice non è quindi un doppione
travestito della qualità — un vino ben giudicato può essere mal protetto e
viceversa. È la condizione che rende la funzionalità utile invece che
decorativa.

Distribuzione risultante:

| | Rossi | Bianchi |
|---|---:|---:|
| Adatto alla conservazione | 30,5% | 84,9% |
| Con monitoraggio | 51,1% | 14,5% |
| Da immettere sul mercato | 18,4% | 0,6% |

### Limiti residui

- **I vini del dataset sono Vinho Verde portoghesi**, prodotti per il consumo
  giovane: una solforosa contenuta è in parte fisiologica e non
  necessariamente un errore di cantina. L'indice segnala un rischio di
  conservazione, non un difetto di lavorazione.
- Mancano annata, condizioni di stoccaggio e temperatura di conservazione,
  che nella realtà pesano quanto la chimica del vino.
- Le soglie adottate (0,5 e 0,8 mg/L di SO₂ molecolare) sono riferimenti
  operativi diffusi, non valori di legge: cantine diverse lavorano con
  margini diversi a seconda dello stile.

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
