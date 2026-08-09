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

## Leve di miglioramento: i limiti dell'analisi a un fattore per volta

La funzionalità implementata in `src/levers.py` risponde alla domanda
operativa che segue la predizione: *su quale parametro conviene intervenire
su questo lotto, e quanto rende*. Per ogni parametro si applica una
correzione realistica, tenendo fermi tutti gli altri, e si osserva come
cambia la previsione del modello.

Tre limiti la accompagnano, dichiarati anche nell'interfaccia accanto ai
risultati.

**È la lettura del modello, non una legge fisica.** Il modello spiega poco
più della metà della variabilità (R² 0,56 sul test set): indica una
tendenza, non un esito garantito.

**Le variabili chimiche sono correlate fra loro.** In cantina non si abbassa
l'acidità volatile "tenendo fermo tutto il resto": ogni intervento ne muove
altri. L'analisi a un fattore per volta ignora le interazioni ed è quindi
**ottimistica** — il guadagno reale sarà tipicamente inferiore a quello
stimato. Un'estensione futura sarebbe valutare combinazioni di due parametri,
al costo di un numero di simulazioni molto maggiore.

**I passi sono scelti, non ottimizzati.** Sono correzioni plausibili in una
lavorazione reale (mezzo grado alcolico, 0,10 g/L di acidità volatile), non
spostamenti statistici. Una sensibilità calcolata su tre deviazioni standard
produrrebbe numeri più grandi e privi di utilità: nessuno in cantina può
dimezzare l'alcol di un vino. La scelta rende l'analisi meno impressionante e
più utilizzabile.

**Assenza di leve è un esito legittimo.** Per alcuni lotti nessuna correzione
a parametro singolo migliora la stima. L'interfaccia lo dichiara invece di
mostrare una lista vuota o di abbassare le soglie fino a trovare qualcosa:
significa che, secondo il modello, il margine non sta in una sola leva.

## Spiegabilità del modello: cosa guida la qualità

Il modello non si limita più a predire: dichiara su quali variabili si basa.
È il tassello che mancava rispetto all'impegno di trasparenza preso nella
dichiarazione etica, dove si afferma che l'utente deve poter capire da dove
viene una stima.

### Metodo

Si usa l'**importanza per permutazione** e non `feature_importances_` del
RandomForest. Quest'ultima si basa sulla riduzione di impurità negli alberi e
ha un difetto noto: sovrastima le variabili con molti valori distinti, perché
offrono più punti di taglio. Su misure di laboratorio come queste — dove ogni
parametro ha centinaia di valori diversi — la distorsione sarebbe rilevante.

L'importanza per permutazione misura invece quanto peggiora la previsione
quando i valori di una variabile vengono mescolati a caso: se rompere una
variabile non peggiora nulla, quella variabile non serviva.

Il calcolo avviene sul **test set**, con la stessa suddivisione usata in
`train.py` (80/20, seed 42, stratificata per tipo). Sui dati di addestramento
l'importanza direbbe cosa il modello ha *usato*; su dati mai visti dice cosa
**generalizza**, che è l'unica cosa utile a chi decide.

### Risultati

| Variabile | Calo di R² | Quota |
|---|---:|---:|
| Grado alcolico | 0,497 | 38,7% |
| Acidità volatile | 0,248 | 19,3% |
| SO₂ libera | 0,135 | 10,5% |
| Solfati | 0,080 | 6,2% |
| SO₂ totale | 0,068 | 5,3% |
| Zucchero residuo | 0,059 | 4,6% |
| pH | 0,046 | 3,6% |
| Acido citrico | 0,044 | 3,4% |
| Cloruri | 0,044 | 3,4% |
| Densità | 0,033 | 2,5% |
| Acidità fissa | 0,031 | 2,4% |
| **Tipo (rosso/bianco)** | **−0,0006** | **≈ 0%** |

**Alcol e acidità volatile pesano insieme il 58%.** Il primo è proxy di
maturazione e corpo, la seconda è un marcatore di deterioramento: il modello
ha imparato che la qualità percepita si gioca soprattutto fra "abbastanza
maturo" e "non difettoso".

**Il tipo di vino non conta.** Il valore è addirittura leggermente negativo,
cioè indistinguibile dal rumore: una volta noto il profilo chimico, sapere se
il vino è rosso o bianco non aggiunge nulla alla previsione. È un risultato
controintuitivo — nel linguaggio comune rosso e bianco sono categorie
opposte — e mostra che la distinzione commerciale è già contenuta nelle
misure analitiche.

### Limiti

- L'importanza per permutazione **sottostima le variabili correlate fra
  loro**: se due parametri portano la stessa informazione, mescolarne uno non
  peggiora molto perché l'altro compensa. La densità, che dipende da alcol e
  zuccheri, ne è l'esempio: il suo 2,5% è probabilmente inferiore al suo peso
  reale.
- L'importanza dice *quanto* una variabile conta, non *in che direzione*. Che
  l'acidità volatile pesi in negativo lo sappiamo dall'enologia, non da questo
  numero.
- I valori si riferiscono a questo modello su questo dataset: non sono una
  legge generale dell'enologia.

## Feature engineering: esperimento con esito negativo

Il progetto calcola diverse grandezze derivate per le regole enologiche, in
particolare l'**SO₂ molecolare** — la frazione di solforosa realmente attiva,
`SO₂ libera / (1 + 10^(pH − 1,81))`. Prese singolarmente, SO₂ libera e pH
pesano poco nella previsione (10,5% e 3,6% di importanza per permutazione);
combinate secondo la chimica producono la grandezza che un enologo osserva
davvero. Era ragionevole attendersi che, fornita già calcolata al modello,
migliorasse la stima della qualità.

### Il risultato

| Configurazione | CV R² | Test R² |
|---|---:|---:|
| Colonne grezze | 0,5000 | 0,5572 |
| + tutte e sei le derivate | 0,5040 | 0,5556 |
| + solo SO₂ molecolare | 0,4985 | 0,5559 |
| + SO₂ molecolare e quota libera | 0,5001 | 0,5517 |

Nessun miglioramento. Le differenze sono nell'ordine dei millesimi, cambiano
segno fra cross-validation e test set, e la **dispersione fra i fold**
(0,005–0,008) è più ampia dello scarto fra le medie: è rumore.

Lo stesso vale per la regressione lineare (0,2924 → 0,2958), usata come
controllo: un modello lineare non può rappresentare rapporti ed esponenziali,
quindi avrebbe dovuto beneficiarne più di un albero. Non è successo, il che
esclude la spiegazione "il RandomForest ci arriva comunque da solo".

### Perché

Non per ridondanza. Il denominatore varia da 9,1 a 159,5 lungo il catalogo,
quindi l'SO₂ molecolare non è un riscalamento della SO₂ libera: correlano
0,854, non 1.

Il motivo è che **quella variabile non ha relazione con il target**:

| Variabile | Correlazione con `quality` |
|---|---:|
| Alcol | +0,444 |
| Acidità volatile | −0,266 |
| SO₂ libera | +0,055 |
| SO₂ molecolare | +0,023 |

L'SO₂ molecolare governa la **tenuta nel tempo** — ossidazione,
rifermentazione — mentre `quality` è un punteggio **sensoriale**: quanto il
vino piace all'assaggio adesso. Sono fenomeni distinti, e un vino può essere
ben protetto e mediocre, oppure fragile ed eccellente. Lo conferma dall'altro
lato la scorrelazione già misurata (0,163) fra indice di conservazione e
punteggio di qualità.

La variabile è quindi corretta, ma per un altro obiettivo — ed è esattamente
dove viene impiegata, in `src/conservation.py`.

Fa eccezione `acidita_totale_stim`, che è un doppione autentico: correla 0,994
con l'acidità fissa.

### Cosa se ne ricava

L'ingegnerizzazione delle variabili non si giudica sulla bontà della formula ma
sulla **pertinenza al fenomeno che il target misura**. Una grandezza corretta,
motivata e chimicamente fondata può non spostare nulla, se descrive qualcosa
che il target non registra.

L'esperimento è riproducibile: `python src/models/feature_experiment.py`.

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

## Il verdetto strutturato non è più vero della risposta libera

Il verdetto di abbinamento (`POST /api/verdetto`) obbliga il modello a
compilare uno schema — giudizio su quattro valori, motivazione, dato citato,
eventuale profilo alternativo — validato con Pydantic, con un solo
ritentativo in caso di output non conforme.

**Cosa garantisce.** Che l'oggetto che arriva all'interfaccia abbia la forma
attesa: nessun campo mancante, nessun giudizio fuori scala, nessun testo
sconfinato. Questo rende il giudizio ordinabile e filtrabile, cosa che una
frase in prosa non è.

**Cosa NON garantisce.** Che il contenuto sia corretto. Uno schema valida la
struttura, non la verità: un modello può compilare `dato_citato` con un numero
plausibile ma sbagliato, e la validazione lo lascia passare. Il campo esiste
per rendere *ispezionabile* l'ancoraggio ai dati — chi legge può confrontare
il valore con la scheda del lotto — non per certificarlo.

**Costo del ritentativo.** Nel caso peggiore latenza e token raddoppiano. Le
metriche mostrate in interfaccia sono cumulative sui tentativi effettuati, e il
numero di tentativi viene dichiarato apertamente: se il modello ha dovuto
essere corretto, è un'informazione sul funzionamento del sistema, non un
dettaglio da nascondere.

**Perché due tentativi e non di più.** Se un modello sbaglia due volte lo
stesso schema dopo essere stato corretto con l'errore ricevuto, il problema
di solito è il modello o il prompt, non la sfortuna: insistere aumenta costo e
attesa senza cambiare l'esito. Il sistema dichiara il fallimento e lascia
disponibile il sommelier in forma libera.

## Quanto funziona davvero il retrieval (misurato)

Il retrieval ibrido era stato scelto su un'ipotesi: senza componente lessicale
il sistema fallirebbe sui nomi di piatti extra-europei, che il modello di
embedding multilingue non rappresenta bene. L'ipotesi ora è misurata su 12
domande con documento atteso dichiarato (`python src/rag/evaluate.py`).

| strategia | hit rate@3 | MRR |
|---|---|---|
| **ibrida** (in uso) | **75%** | **0.653** |
| solo semantica | 42% | 0.361 |
| solo lessicale | 58% | 0.542 |

**L'ipotesi regge, e in modo più netto del previsto.** Il semantico puro
fallisce su `ndole` e su "piatto africano" — esattamente i casi per cui la
componente lessicale è stata scritta. Il bias culturale del modello di
embedding non è una preoccupazione teorica: si vede nei numeri.

**Il risultato più interessante è che il semantico puro è la strategia
peggiore**, sotto anche al lessicale. Su una knowledge base piccola, in
italiano e con vocabolario tecnico, la corrispondenza per radice di parola è
più informativa della vicinanza vettoriale prodotta da un modello multilingue
generalista. È un promemoria contro l'automatismo "embedding = moderno =
migliore": la scelta dipende dalla dimensione e dalla lingua del corpus, non
dalla novità della tecnica.

**Cosa fallisce ancora.** Tre domande sbagliano con ogni strategia: carbonara,
tiramisù, prosciutto crudo. Il motivo è comune — sono nomi di piatti, e la
knowledge base è scritta per **sensazioni** (grassezza, tendenza dolce,
sapidità), non per ricette. Nessun aggiustamento del retrieval può colmare
questo divario: manca il passaggio da piatto a sensazione, che oggi resta a
carico dell'LLM in fase di generazione. Aggiungere alla knowledge base un
documento che mappi piatti comuni alle rispettive sensazioni chiuderebbe la
lacuna, e sarebbe un intervento sui dati, non sull'algoritmo.

**Limite della misura.** Dodici domande scritte a mano, con ground truth
scelta da chi ha scritto la knowledge base. Un divario di 33 punti è troppo
ampio per essere rumore, ma questi numeri non sono una validazione statistica:
servono a smascherare fallimenti netti, non a certificare una percentuale.

## L'agente sul catalogo: cosa garantisce e cosa no

`POST /api/agente` dà al modello due strumenti (`cerca_vini`, `scheda_lotto`)
e ne esegue le chiamate. Il modello sceglie quale strumento usare e con quali
argomenti; non scrive SQL, non tocca il database, e i limiti — massimo 20
risultati, filtri consentiti — restano nel codice anche quando il modello
chiede altro.

**Cosa questo elimina.** L'invenzione di lotti, prezzi e gradazioni. Prima, a
una domanda sul catalogo il modello rispondeva a memoria: in modo fluente e
indistinguibile da una risposta vera. Ora i numeri che cita provengono da una
query, e l'interfaccia mostra quale.

**Cosa NON elimina.** Il modello può ancora scegliere lo strumento sbagliato o
tradurre male la domanda in filtri — chiedere i rossi e filtrare i bianchi,
o interpretare "economici" con una soglia arbitraria. Il function calling
sposta l'errore dall'invenzione del dato alla **formulazione della domanda**:
è un errore più raro e, soprattutto, visibile, perché i filtri usati sono
mostrati accanto alla risposta. Chi legge può accorgersene; con una risposta
inventata non poteva.

**Costo.** Ogni giro del ciclo è una chiamata a pagamento. Il tetto è quattro
giri: oltre, si dichiara il fallimento invece di restituire una risposta
parziale.

## Il 29% del punteggio del modello era memoria, non predizione

Per gran parte dello sviluppo il progetto ha dichiarato R² 0.522 in
cross-validation e 0.561 su test set. Erano numeri gonfiati, e la causa non
era nel modello ma nei dati.

**Cosa è successo.** Il Wine Quality dell'UCI contiene **1.177 righe
perfettamente identiche su 6.497 — il 18% del dataset**. `train_test_split`
divide a caso: una riga finisce in addestramento e la sua copia esatta in
test. Il modello viene interrogato su dati che ha già memorizzato, e la
memorizzazione è precisamente ciò che una Random Forest fa meglio.

È data leakage, ma non del tipo che una `Pipeline` può prevenire: il
preprocessing era corretto: il problema stava nella composizione dei dati.

**La misura** (`python src/models/leakage_experiment.py`):

| scenario | RMSE | MAE | R² |
|---|---|---|---|
| A. split casuale (com'era) | 0.569 | 0.403 | **0.561** |
| C. raggruppato, nessuna fuga | 0.679 | 0.528 | **0.398** |
| B. deduplicato | 0.675 | 0.515 | 0.373 |

Il confronto che conta è **A contro C**, non A contro B. Deduplicare cambia
due cose insieme — elimina la fuga *e* riduce il dataset del 18% — quindi un
calo dell'R² non direbbe quale delle due l'ha causato. Lo scenario C tiene
tutte le righe e impedisce solo alle copie di attraversare lo split
(`GroupShuffleSplit` sulla firma chimica): stessa quantità di dati, zero fuga.
La differenza isolata è **R² −0.163, il 29% del punteggio dichiarato**.

**La cross-validation non protegge.** È il punto meno intuitivo:
`KFold(shuffle=True)` sparge le copie fra i fold esattamente come uno split
casuale. La CV difende dalla sfortuna di una singola divisione, non dalla
contaminazione dei dati.

| cross-validation | R² |
|---|---|
| KFold con shuffle (contaminata) | 0.521 |
| GroupKFold sulla firma chimica | **0.385** |

**Correzione applicata.** `src/models/train.py` usa ora `GroupKFold` e
`GroupShuffleSplit`. Si raggruppa invece di deduplicare per non buttare il 18%
dei dati: le copie restano utili in addestramento, devono solo smettere di
comparire in valutazione. Si perde la stratificazione per tipo, ed è un prezzo
accettabile — l'assenza di fuga vale più di una ripartizione rosso/bianco
perfetta.

**Cosa insegna questo episodio.** L'EDA è stata fatta dopo il modello, non
prima, perché si è dato per scontato che un dataset accademico pubblicato e
citato fosse pulito. Nessuna quantità di rigore a valle — Pipeline corretta,
cross-validation, confronto fra algoritmi, permutation importance — ha
intercettato un problema che stava a monte. Tre righe di `pandas` all'inizio
lo avrebbero mostrato subito.

**Nota su un'ipotesi smentita.** Cercando i duplicati si era ipotizzato di
trovare vini con chimica identica e voto diverso, cioè assaggiatori in
disaccordo, il che avrebbe imposto un tetto teorico all'R² raggiungibile. Il
dato dice zero: a chimica identica corrisponde sempre lo stesso voto. I
duplicati sono copie esatte, non giudizi discordanti — innocui per la coerenza
del target, pericolosi per la valutazione.

## Esplorazione del dataset

`python src/eda.py` produce i numeri e i grafici in `docs/eda/`.

**Distribuzione del target.** Le sole classi 5 e 6 valgono il **76,6%** del
dataset; la qualità 9 ha 5 esempi, la 3 ne ha 30. Un modello che predicesse
sempre 5,6 sbaglierebbe poco: è il riferimento minimo contro cui va giudicato
ogni risultato, e spiega perché un R² di 0.4 su questo dataset non è il
fallimento che sembrerebbe altrove.

**Correlazioni con la qualità.** L'alcol guida (+0.444), seguito da densità
(−0.306) e acidità volatile (−0.266). Le altre otto variabili stanno tutte
sotto 0.21 in valore assoluto. Densità e alcol sono fortemente legate fra
loro, il che va tenuto presente leggendo la permutation importance: fra
variabili correlate l'importanza si divide, e una può sembrare inutile solo
perché l'altra la copre.

**Valori anomali.** Oltre 1.5 IQR: acido citrico 7,8%, acidità volatile 5,8%,
acidità fissa 5,5%. **Non vengono rimossi.** In enologia un valore estremo è
spesso un lotto reale e problematico, non un errore di misura — ed è
esattamente il lotto che interessa a chi lavora in cantina. Toglierli
renderebbe il modello più accurato sulla media e cieco proprio dove serve.

## La fuga non premiava tutti i modelli allo stesso modo

Scoperto il leakage, restava una domanda: il confronto fra algoritmi che ha
portato a scegliere la Random Forest era anch'esso viziato?

L'ipotesi era che sì, e in modo *asimmetrico*. Una `LinearRegression` non può
memorizzare una singola riga: non ne ha la capacità, può solo tracciare un
piano. Una Random Forest con 200 alberi può, ed è precisamente ciò che fa
meglio. Se è così, la fuga non falsa solo i valori assoluti ma il **confronto**
— premiando i modelli ad alta capacità.

`python src/models/compare_models.py` esegue lo stesso confronto due volte,
con `KFold(shuffle=True)` e con `GroupKFold`:

| modello | R² contaminato | R² raggruppato | guadagno |
|---|---|---|---|
| RandomForest | 0.521 | 0.385 | **+0.136** |
| GradientBoosting | 0.390 | 0.364 | +0.026 |
| LinearRegression | 0.292 | 0.289 | +0.003 |

**Un fattore 47 fra il primo e l'ultimo.** L'ipotesi era corretta: il beneficio
della fuga è proporzionale alla capacità di memorizzare del modello.

**La classifica non cambia** — la Random Forest resta prima anche senza fuga,
quindi la scelta dell'algoritmo regge. Ma il *margine* era gonfiato molto più
dei valori assoluti:

| confronto | vantaggio RF contaminato | vantaggio RF reale |
|---|---|---|
| contro LinearRegression | 0.229 | **0.095** |
| contro GradientBoosting | 0.131 | **0.021** |

Contro il GradientBoosting il vantaggio quasi sparisce: 0.021 di R², con uno
scarto tipo di 0.015 sull'RMSE fra i fold. La Random Forest resta preferibile,
ma la formula "nettamente migliore" che compariva nella documentazione non è
più sostenibile ed è stata rimossa.

**Perché questo caso merita attenzione.** Il leakage viene di solito
presentato come un problema di metriche gonfiate — sgradevole ma innocuo, si
corregge il numero e si va avanti. Qui ha rischiato di alterare una
**decisione**: se il divario reale fosse stato negativo invece che +0.021, il
progetto avrebbe adottato l'algoritmo sbagliato sulla base di una misura
corretta nella forma e falsa nella sostanza.

## Metriche finali, misurate senza fuga

```
5-fold CV raggruppata   RMSE 0.684 (+/- 0.015)   MAE 0.525   R2 0.385
Test set (1310 vini)    RMSE 0.680               MAE 0.528   R2 0.397
```

CV e test set concordano (0.385 e 0.397): il modello non è né fortunato né
sfortunato nella divisione scelta.

**Come leggere un R² di 0.4.** Sembra basso, e in assoluto lo è, ma va
confrontato con il riferimento giusto: il 76,6% dei vini sta nelle classi 5 e
6, quindi predire sempre "5,6" sbaglierebbe poco. Su un target così compresso
e con sole variabili chimiche — senza vitigno, annata, zona, vinificazione —
spiegare il 40% della varianza è un risultato coerente con la letteratura su
questo dataset. Il numero onesto è più utile di quello gonfiato: dice a chi
usa la piattaforma quanto fidarsi di una previsione.

## Anche la spiegazione del modello era contaminata

L'importanza per permutazione (`src/importance.py`) si calcola su un test set:
si mescola una colonna e si osserva quanto peggiora la previsione. Se quel
test set contiene righe già viste in addestramento, si sta misurando quanto la
permutazione rompe la **memoria**, non quanto danneggia la capacità di
generalizzare — che è la domanda che ci si sta ponendo.

Il file dichiarava in testa di replicare lo split di `train.py`. Non era più
vero da quando `train.py` era passato a `GroupShuffleSplit`: una promessa di
allineamento scritta e violata. Ora la funzione di raggruppamento viene
**importata** da `train.py` invece di essere riscritta, così le due non
possono più divergere.

**Effetto della correzione.** Tutte le importanze calano, ma non in
proporzione:

| variabile | contaminata | pulita | calo |
|---|---|---|---|
| alcohol | 0.691 | 0.402 | −42% |
| volatile_acidity | 0.369 | 0.161 | −56% |
| free_sulfur_dioxide | 0.237 | 0.106 | −55% |
| sulphates | 0.141 | 0.045 | −68% |
| total_sulfur_dioxide | 0.123 | 0.028 | −77% |
| pH | 0.094 | 0.012 | **−87%** |
| fixed_acidity | 0.064 | 0.008 | **−87%** |

Il meccanismo: su una riga memorizzata, permutare *qualunque* colonna rompe il
riconoscimento e fa crollare la previsione. La fuga gonfia quindi l'importanza
di tutto, e in termini relativi gonfia soprattutto le variabili deboli — che
senza fuga non contribuiscono quasi nulla.

**Conseguenze pratiche.** Il pH scende dal sesto al decimo posto: è l'unico
cambio di ordine rilevante, e pesa perché il pH è un parametro a cui in
cantina si guarda molto. La sua importanza era in buona parte un artefatto.

E la spiegazione si semplifica: le prime tre variabili passano dal 63% al
**78%** dell'importanza totale. Il messaggio operativo diventa più netto —
alcol, acidità volatile e SO₂ libera, il resto è contorno.

**Perché questo è il caso più serio dei tre.** Metriche gonfiate ingannano chi
valuta il progetto. Un confronto fra algoritmi viziato può portare a scegliere
il modello sbagliato. Ma un'importanza gonfiata arriva **all'utente finale**:
la pagina che dice a una piccola cantina su quali parametri intervenire. Un
enologo che avesse letto quella tabella avrebbe lavorato sul pH credendolo
rilevante quanto i solfati.

## Il divario fra piatti e sensazioni, e cosa ha insegnato

La valutazione del retrieval mostrava tre domande che fallivano con **ogni**
strategia: carbonara, tiramisù, prosciutto crudo. Diagnosi: la knowledge base
descrive sensazioni, chi domanda nomina piatti. Lacuna nei dati, non
nell'algoritmo.

Correzione: un documento che scompone i piatti comuni nelle rispettive
sensazioni. Non aggiunge regole — costruisce il ponte fra il linguaggio di chi
chiede e quello del corpus.

**Perché NON una tabella esaustiva di abbinamenti.** Sarebbe stata la scelta
istintiva, e avrebbe contraddetto il metodo del progetto: la knowledge base si
regge sulla scomposizione sensoriale, ed è per questo che il sistema sa
affrontare il *ndole*, che in nessun ricettario italiano comparirà. Una tabella
sostituisce il ragionamento con la ricerca a indice e fallisce sul primo piatto
non elencato. Inoltre, come mostrato sotto, un solo documento in più aveva già
saturato il contesto: centinaia di voci l'avrebbero monopolizzato.

### La misura che ha impedito di dichiarare un successo falso

Aggiunto il documento, il primo risultato sembrava trionfale: **hit rate 100%**.
Ma il punteggio calcolato sulla ground truth originale — mai modificata — era
**sceso** dal 75% al 67%.

Era il sintomo di un peggioramento reale: il documento nuovo occupava i primi
posti e i documenti sensoriali restavano fuori. L'LLM avrebbe ricevuto la
scomposizione del piatto **senza la regola di abbinamento**.

Tenere due riferimenti — quello dichiarato prima di vedere i risultati e quello
allargato ai documenti aggiunti dopo — è ciò che ha reso visibile la
differenza. Con la sola metrica allargata, il peggioramento sarebbe stato
presentato come un 100% di successo.

### Due ipotesi sbagliate, risolte guardando i dati

**Prima ipotesi:** un documento lungo produce molti chunk e monopolizza i
posti. Implementata la diversificazione dei risultati (al massimo un chunk per
documento): l'hit rate è passato da 67% a 67%. **Nessun effetto.** La
diversificazione è stata tenuta perché corretta in sé, ma non era il problema.

**Seconda ipotesi:** il documento nuovo scalza quelli sensoriali. Stampando
cosa veniva effettivamente recuperato si è visto che per "carbonara" ai posti
2 e 3 c'erano *Dolcezza* e *Tendenza amara* — documenti irrilevanti. Fra i
documenti sensoriali l'ordinamento è sostanzialmente **rumore**: non
contengono nomi di piatti, quindi la componente lessicale non ha appigli e il
modello semantico non discrimina.

La regressione reale era **una sola** domanda (bistecca al sangue). Le altre
tre fallivano già da prima.

### La soluzione: misurare quanti passaggi servono

| top_k | hit stretto | hit ampio |
|---|---|---|
| 3 | 67% | 100% |
| 4 | 75% | 100% |
| **5** | **92%** | 100% |
| 6 | 92% | 100% |

I documenti sensoriali venivano recuperati, ma in quarta e quinta posizione —
ed è per questo che l'MRR migliora poco (0.542 → 0.596) mentre l'hit rate
migliora molto.

`top_k = 5` è il ginocchio della curva. Costo misurato: **1.530 token di
prompt contro 1.370**, cioè +12% per +17 punti di hit rate. Il semantico puro
guadagna anche di più (42% → 67%): era la strategia che più soffriva i tre
posti stretti.

**Avvertenza sul 92%.** Il valore di `top_k` è stato scelto guardando le
stesse 12 domande su cui viene poi misurato: è una stima ottimistica, non un
risultato su dati mai visti. È la versione in piccolo dello stesso errore
trovato nel dataset del modello. Per una stima onesta servirebbe un secondo
insieme di domande, tenuto da parte e mai consultato durante le scelte di
progettazione — ed è il miglioramento più utile che questa valutazione possa
ricevere.

## Un insieme di valutazione più grande, e cosa è costato costruirlo

Tutte le misure sul RAG erano fatte su **12 domande scritte a mano**. Con 12
domande una sola risposta sbagliata vale 8 punti percentuali: si è discusso di
uno scarto fra 67% e 75% che era, letteralmente, una domanda. Nessuna delle
decisioni prese su quei numeri era statisticamente sostenuta.

### Come sono state prodotte

Per ogni passaggio della knowledge base si chiede al modello: *"quale domanda
farebbe un vignaiolo, se questo testo fosse la risposta?"*. La ground truth è
automatica — il documento da cui la domanda nasce — ed è l'unico motivo per
cui se ne possono generare decine senza etichettarle una per una.

**Il rischio, dichiarato prima di misurarlo.** Una domanda generata da un testo
tende a riusarne le parole, e il retrieval ibrido di questo progetto si regge
anche sulla corrispondenza lessicale: un insieme così costruito la
avvantaggerebbe artificialmente. Due contromisure — il prompt vieta i termini
tecnici del passaggio, e lo script *misura* la sovrapposizione lessicale.
Risultato: **0,12 di media**, una sola domanda sopra 0,50. La contromisura ha
funzionato.

### Tre problemi trovati, tutti nei dati e non nel codice

**1. Squilibrio (61,5% su un documento).** Il documento sui piatti è più lungo,
produce più chunk, genera più domande. L'insieme aveva ereditato la
**struttura della knowledge base** invece di rispecchiare le domande reali.
Corretto con un tetto di 8 domande per documento, scartando per prime quelle
con sovrapposizione lessicale più alta.

**2. Ground truth sbagliata nel 13% dei casi** (5 su 38). Il presupposto —
*"il chunk che ha ispirato la domanda è quello che la risponde meglio"* — è
falso. Tutti gli errori nello stesso verso: il modello, davanti a un passaggio
teorico, scriveva comunque domande su piatti concreti.

| domanda | atteso automatico | corretto |
|---|---|---|
| "tagliere di salumi molto unti" | Principio fondamentale | Grassezza e untuosità |
| "secco o dolce per il dessert" | Principio fondamentale | Dolcezza |
| "sushi molto speziato" | Esempio ndole | Tendenza amara e piccantezza |

Altre 5 domande sono state scartate: due quasi-duplicati e tre troppo vaghe
(*"Ho una cena importante stasera, come scelgo il vino?"* ha per risposta
l'intera knowledge base).

**3. I documenti teorici restavano scoperti.** Dopo le correzioni, "Principio
fondamentale" aveva **una sola** domanda. Non è sfortuna: un generatore che
parte dai documenti produce le domande che i documenti *suggeriscono*, non
quelle che al corpus mancano. Le domande sul metodo — *"il vino deve
assomigliare al piatto o fare da contrasto?"* — non le scrive mai, perché non
è così che parlano le persone davanti a un testo su un piatto. Aggiunte 9
domande a mano, con sovrapposizione lessicale 0,17 contro 0,12 delle generate:
leggermente più facili, quindi senza svantaggio artificiale sui documenti che
coprono.

### Due insiemi: sviluppo e verifica

Le 47 domande sono divise in **sviluppo** (36, su cui si tarano i parametri) e
**verifica** (11, consultato solo per dichiarare un risultato). È la
correzione del difetto documentato più sopra: `top_k` era stato scelto
guardando le stesse domande su cui veniva poi misurato.

La divisione è **deterministica**, calcolata dall'hash del testo di ogni
domanda: aggiungerne di nuove non sposta le esistenti fra i due insiemi, che
renderebbe incomparabile ogni misura precedente.

| insieme | n | hit@5 | MRR |
|---|---|---|---|
| sviluppo | 36 | 89% | 0,485 |
| **verifica** | 11 | **91%** | 0,571 |

**Verifica non è più basso di sviluppo.** Le scelte fatte guardando il primo
reggono su domande mai viste: nessun segno di adattamento al set di sviluppo.

**Limite residuo, e non è piccolo.** Undici domande di verifica sono poche —
una vale 9 punti percentuali. La concordanza fra i due insiemi è
rassicurante, non è una prova. E la ground truth resta decisa da chi ha
scritto la knowledge base: un giudizio esterno la sposterebbe in modi che non
possiamo prevedere.

**Cosa insegna, in una riga.** La generazione sintetica fa risparmiare la
scrittura delle domande, non il giudizio su quale sia la risposta giusta.
