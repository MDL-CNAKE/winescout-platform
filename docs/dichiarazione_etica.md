# Dichiarazione etica

WineScout / CruScout è uno strumento di supporto per piccole cantine: stima la
qualità di un lotto dalla sua analisi chimica, ne descrive la conservazione,
propone abbinamenti e risponde a domande attraverso un modello linguistico.

Questo documento dice cosa il sistema fa, cosa **non** fa, quali dati tocca e
dove sbaglia. È scritto per essere letto da chi lo usa, non da chi lo valuta.

---

## 1. Dati e privacy

### Cosa viene salvato sul tuo dispositivo

**Con l'interfaccia Streamlit, niente.** L'operatore scelto e la
conversazione con SVEVA restano nella memoria della sessione sul server e si
perdono alla chiusura della pagina.

**Con il frontend React, una cosa sola:** quale operatore hai selezionato,
per non doverlo riscegliere a ogni pagina. È una preferenza che hai espresso
tu, non un identificativo che ti segue.

**Nessun cookie. Nessun analytics. Nessun tracciamento.** Non ci sono banner
di consenso perché non c'è niente da consentire: il sistema non raccoglie
statistiche di navigazione, non profila e non chiama servizi di terze parti
per misurare cosa fai.

### Cosa NON viene conservato sul server

La conversazione con SVEVA vive nella sessione dell'interfaccia (in memoria
con Streamlit, nel browser con React). Lo storico viene rimandato al
backend a ogni domanda perché il modello possa capire i seguiti — *"e con il
pesce?"* — ma non viene mai salvato: **chi chiude la pagina ha chiuso davvero
la conversazione.** Non esiste un archivio delle domande poste, e questa è una
scelta, non una dimenticanza.

Ha un costo: non possiamo dirti quali abbinamenti vengono chiesti più spesso,
e infatti la sezione Marketing dichiara quella funzione come non disponibile
insieme al dato che le servirebbe. Registrare le conversazioni la
sbloccherebbe, ed è una decisione che spetta alla cantina — da prendere
apertamente, non di nascosto.

### Cosa esce da casa tua

**Le domande poste a SVEVA vengono inviate a un modello linguistico esterno**
(OpenRouter). Insieme alla domanda partono i dati del lotto selezionato — nome
descrittivo, valori chimici, prezzo — e i passaggi recuperati dalla knowledge
base.

Questo va saputo prima di scrivere qualcosa di riservato in quella casella. Il
fornitore ha le proprie condizioni d'uso, che non controlliamo. Se la
riservatezza fosse un requisito, la strada sarebbe un modello eseguito in
locale: costa in qualità delle risposte e in risorse macchina, e sarebbe una
scelta consapevole invece di una sorpresa.

Tutto il resto — catalogo, predizioni, conservazione, packaging, ricerca nella
knowledge base — avviene sulla vostra installazione, senza uscire.

### Operatori

I nomi degli operatori sono **etichette di lavoro** scelte dalla cantina, non
identità verificate. Servono a mostrare a ciascuno gli strumenti del proprio
mestiere e ad attribuire le selezioni condivise. Non c'è autenticazione:
chiunque può cambiare operatore. **Non è un sistema di permessi e non va usato
come tale.**

### Font e risorse

I caratteri tipografici sono ospitati insieme all'applicazione, non caricati da
una CDN esterna. Il browser non invia richieste a terzi durante la navigazione
normale.

---

## 2. Cosa il sistema non sa, e lo dice

Il principio che attraversa tutto il progetto: **dove il dato manca, si
dichiara invece di dedurlo.**

**Vitigno, annata, terroir.** Il dataset di origine (UCI Wine Quality, Cortez
et al. 2009) contiene undici misure chimiche e un punteggio. Non contiene il
vitigno. Per questo il catalogo usa nomi *descrittivi* derivati dalla chimica —
"Rosso Corposo Armonico – Lotto #0042" — e il sommelier ha il divieto esplicito
di associare un vitigno a un lotto. Un nome plausibile ma inventato è
un'informazione falsa, anche se suona bene.

**"Riserva".** Nel diritto vitivinicolo italiano indica un affinamento minimo
fissato dal disciplinare. Il dataset non sa nulla di affinamento, quindi la
menzione non compare: usarla come sinonimo di "punteggio alto" sarebbe una
promessa non verificabile.

**"Conservazione", non "invecchiamento".** L'indice valuta SO₂ molecolare,
acidità volatile, pH e quota di solforosa libera. Non può vedere tannini,
struttura polifenolica o potenziale evolutivo: dice quali lotti conviene far
uscire prima, non per quanti anni un vino reggerà.

**Preferenze di mercato.** Non sono deducibili dalla chimica. Il sistema le fa
**dichiarare** a chi le conosce, invece di inventarle.

**Prezzo e margine sono simulati.** Il dataset è puramente analitico. Prezzi e
margini sono generati da una logica esplicita (`src/pricing.py`) e dichiarati
come tali nell'interfaccia. Non sono listini reali, e nessuna analisi
commerciale è costruita su di essi come se lo fossero.

---

## 3. Quanto è affidabile, in numeri

**Il modello spiega circa il 40% della variabilità dei punteggi.**

| misura | valore |
|---|---|
| 5-fold CV raggruppata | R² 0,385 — RMSE 0,684 |
| test set senza righe ripetute | R² 0,397 — RMSE 0,680 |

Questi numeri sono **più bassi di quelli dichiarati per gran parte dello
sviluppo** (0,52 e 0,56). Non perché il modello sia peggiorato, ma perché i
primi erano gonfiati: il dataset contiene 1.177 righe perfettamente duplicate
su 6.497, e uno split casuale ne mandava una in addestramento e la copia in
test. Il 29% del punteggio veniva dall'aver rivisto righe già memorizzate.

L'abbiamo scoperto, misurato e corretto — l'analisi completa è in
[model_limitations.md](model_limitations.md). **Il numero onesto è più utile di
quello lusinghiero:** dice a chi usa la piattaforma quanto fidarsi.

**Come leggere un R² di 0,40.** Il 77% dei vini sta in due sole classi (5 e 6):
predire sempre "5,6" sbaglierebbe poco. Su un target così compresso, con le
sole variabili chimiche, spiegare il 40% della varianza è coerente con la
letteratura su questo dataset. Il modello coglie la tendenza generale e sbaglia
di più agli estremi, dove gli esempi sono pochissimi — 30 vini di qualità 3,
cinque di qualità 9.

**Il recupero della knowledge base** trova il documento pertinente nell'89-91%
delle domande di prova (47 domande, insieme di verifica tenuto separato).

---

## 4. Il bias, e cosa è stato fatto

**Bias del dataset.** Solo vini portoghesi fermi della regione Vinho Verde:
nessun rosato, nessuno spumante, nessuna altra denominazione. Fuori da quel
dominio il sistema non fornisce stime.

**Bias del modello linguistico.** Il modello di embedding multilingue è
addestrato prevalentemente su testi occidentali e rappresenta male i nomi di
piatti extra-europei. Non è un timore teorico: **è misurato.** La ricerca
puramente semantica fallisce su "ndole" e su "piatto africano", mentre la
ricerca ibrida (semantica + lessicale) li trova. Senza quella componente il
sistema sarebbe peggiore proprio sulle cucine non occidentali.

Per la stessa ragione la knowledge base è costruita sulle **sensazioni**
(grassezza, sapidità, tendenza amara) e non su ricettari: le sensazioni
attraversano le cucine, i ricettari no. È ciò che permette di affrontare un
piatto che in nessun manuale italiano comparirà mai.

**Bias di chi ha scritto.** La knowledge base, le regole enologiche e le
domande di valutazione sono state scritte da noi. La ground truth della
valutazione riflette il nostro giudizio su quale documento risponda meglio: un
lettore esterno la sposterebbe in modi che non possiamo prevedere. È un limite
dichiarato, non risolto.

---

## 5. Dove il sistema sbaglia, in chiaro

- **Le leve di miglioramento indicano correlazioni, non cause.** Il modello ha
  imparato che certi valori accompagnano punteggi alti; non sa che
  modificandoli il vino migliori. In cantina un parametro non si muove da solo.
- **L'importanza delle variabili non è una spiegazione causale.** Dice quanto
  la previsione peggiora rompendo una variabile, su questo dataset.
- **L'output strutturato garantisce la forma, non la verità.** Un verdetto di
  abbinamento può citare un dato plausibile ma sbagliato: la validazione
  controlla che il campo ci sia, non che sia corretto. Per questo il dato
  citato è mostrato accanto alla scheda del lotto, così chi legge può
  confrontarlo.
- **L'agente può tradurre male una domanda in filtri.** Il function calling
  elimina l'invenzione dei numeri, non l'errore di interpretazione — che però
  è visibile, perché i filtri usati sono mostrati.

---

## 6. Inquadramento normativo

**EU AI Act — rischio minimo.** Il sistema è un supporto decisionale: non
prende decisioni autonome o vincolanti, non incide su diritti fondamentali,
non valuta persone. Le stime accompagnano il giudizio di chi lavora in
cantina, non lo sostituiscono.

**GDPR.** Nessun dato personale nel dataset, che contiene misure chimiche
pubbliche. L'unico dato conservato lato utente è una preferenza funzionale.
Le conversazioni non sono archiviate.

**Direttiva ePrivacy.** Nessun cookie, nessun consenso richiesto, nessun
banner: non c'è tracciamento da autorizzare.

**Reg. UE 2019/33.** Le soglie di dolcezza usate nella denominazione dei lotti
seguono la normativa europea, non valori scelti a piacere.

---

## 7. Una nota sul metodo

Diversi limiti elencati qui non erano noti all'inizio: sono stati **trovati
misurando**, spesso smentendo ciò che ci aspettavamo. Il leakage nel dataset,
il documento che peggiorava il recupero mentre il punteggio saliva al 100%, la
ground truth automatica sbagliata nel 13% dei casi.

Ogni volta la scoperta è arrivata da una misura che poteva dare torto, non da
una che poteva solo confermare. È il motivo per cui questo documento contiene
più cose che non funzionano che cose che funzionano: **un sistema di cui si
conoscono i difetti è più affidabile di uno che non ne dichiara nessuno.**
