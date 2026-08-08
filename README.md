# CruScout - Il cruscotto del piccolo produttore

> Dagli algoritmi al calice. Senza storie di fantasia.

Applicazione per piccole cantine artigianali. Il catalogo e' il punto di
partenza; da li' ogni referenza apre su predizione della qualita', leve di
miglioramento, predisposizione alla conservazione, raccomandazioni, packaging
e sommelier virtuale.

Ogni contenuto mostrato deriva dai dati reali del vino (profilo chimico, qualita
misurata, regole enologiche): nessuna descrizione redazionale inventata. Dove il
dato non c'e', il sistema lo dichiara invece di colmarlo — non nomina vitigni,
non promette potenziale di invecchiamento, non deduce preferenze di mercato.

Le funzioni sono organizzate per **ruolo operativo**: titolare, enologo,
vendite e logistica vedono in navigazione gli strumenti del proprio mestiere.

Progetto sviluppato per l'esame "Strumenti AI e Machine Learning - Python".

## Stack tecnico

- Python 3.11+, FastAPI (API REST)
- React + TypeScript, TanStack Router/Query, Recharts (interfaccia)
- MySQL 8.4, migrazioni versionate con Flyway
- scikit-learn (Pipeline, RandomForestRegressor)
- RAG su knowledge base enologica (ricerca ibrida semantica + lessicale)
- LLM via OpenRouter API (sommelier virtuale, con modalita demo se manca la chiave)
- Docker / docker-compose (mysql + flyway + backend + frontend)
- Streamlit mantenuto come demo di riserva (profilo `legacy`)

## Dataset

Wine Quality Dataset di Cortez et al. (UCI ML Repository) - 6497 vini portoghesi
(1599 rossi, 4898 bianchi), 11 feature chimiche + punteggio qualita (3-9).

## Avvio rapido (Docker, consigliato)

Richiede Docker e Docker Compose installati.

    docker compose up --build

Questo comando:
1. avvia MySQL con un volume persistente
2. esegue le migrazioni Flyway (schema + seed di 6497 vini)
3. builda e avvia il backend FastAPI su http://localhost:8000 (documentazione
   interattiva su `/docs`)
4. builda e avvia il frontend React su http://localhost:5174

Per fermare tutto: `docker compose down` (i dati restano nel volume).
Per ripartire da zero: `docker compose down -v` (cancella anche i dati).

Per attivare il Sommelier Virtuale con un LLM reale, copia `.env.example` in `.env`
e imposta `OPENROUTER_API_KEY`. Senza chiave l'app funziona comunque in modalita demo.

## Avvio in locale (sviluppo, senza Docker per l'app)

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env

    # avvia solo mysql + flyway
    docker compose up -d mysql
    docker compose up flyway

    # genera/rigenera il modello (opzionale, ne esiste gia' uno addestrato)
    python src/models/train.py

    # backend (terminale 1)
    uvicorn backend.main:app --reload --port 8000

    # frontend (terminale 2)
    cd frontend && npm install && npm run dev

## Struttura del progetto

    winescout-platform/
    |
    winescout-platform/
    |
    |-- backend/
    |   `-- main.py                   # API FastAPI: catalogo, ricerca, predizione, conservazione,
    |                                 #   leve, importanza, packaging, profili, operatori, sommelier
    |
    |-- frontend/
    |   |-- nginx.conf                # Fallback SPA (try_files): evita il 404 sul refresh delle rotte
    |   `-- src/
    |       |-- api.ts                # Client API tipizzato (axios), unico punto di contatto col backend
    |       |-- router.tsx            # Rotte a codice (TanStack Router), layout e sezioni per ruolo
    |       |-- index.css             # Tema scuro, identita' visiva, layout responsive
    |       |-- context/
    |       |   `-- OperatoreContext  # Operatore corrente condiviso: con lo stato dentro l'hook
    |       |                         #   ogni componente ne aveva una copia disallineata
    |       |-- hooks/
    |       |   `-- useFavorites      # Selezioni di lavoro condivise, lette dal database
    |       |-- lib/
    |       |   `-- wineLabel.ts      # Nome, lotto e descrittori derivati dal nome in database
    |       |-- components/           # BottleIcon (bottiglia disegnata dai dati), WineGridCard,
    |       |                         #   FilterBar, Pagination, ChemicalRadar, ImportanzaVariabili,
    |       |                         #   ConservazioneScheda, LeveScheda, ValidationNote, EmptyState
    |       `-- routes/
    |           |-- Home.tsx          # Catalogo in griglia: filtri chimici, ordinamento, paginazione
    |           |-- Vino.tsx          # Scheda vino: sidebar + cinque schede contestuali
    |           |-- Predizione.tsx    # Stima da valori di laboratorio propri + importanza variabili
    |           |-- Conservazione.tsx # Magazzino ordinato per rischio di conservazione
    |           |-- Vendite.tsx       # Profili di mercato e margini
    |           |-- Packaging.tsx     # Galleria packaging per stile
    |           |-- Spedizioni.tsx    # Sezione in arrivo (ruolo logistica)
    |           `-- Sommelier.tsx     # SVEVA, sommelier virtuale
    |
    |-- src/
    |   |-- app.py                    # Entry point Streamlit (demo di riserva, profilo legacy)
    |   |-- data_loader.py            # Scarica e unisce il Wine Quality Dataset (UCI)
    |   |-- generate_seed.py          # Converte il CSV in seed SQL versionato (V2)
    |   |-- wine_style.py             # Soglie di dolcezza (Reg. UE 2019/33), corpo, acidita' percepita
    |   |-- naming.py                 # Nomi descrittivi dai dati chimici (V4)
    |   |-- pricing.py                # Prezzo e margine simulati con logica di business (V3)
    |   |-- pairing.py                # Abbinamenti da regole enologiche (V5)
    |   |-- conservation.py           # Indice di predisposizione alla conservazione (a regole)
    |   |-- levers.py                 # Leve di miglioramento: analisi controfattuale sul modello
    |   |-- importance.py             # Importanza per permutazione, calcolata sul test set
    |   |-- database/
    |   |   `-- connection.py         # DatabaseConnection: context manager, logging, gestione errori
    |   |-- rag/                      # Knowledge base sensoriale, indice e recupero ibrido
    |   `-- models/
    |       |-- compare_models.py     # Confronto RandomForest/GradientBoosting/LinearRegression, 5-fold CV
    |       |-- train.py              # Training finale: Pipeline sklearn, CV + test set, joblib
    |       `-- recommender.py        # WineRecommender: content-based con similarita' coseno
    |
    |-- scripts/
    |   `-- test_db_connection.py     # Verifica rapida della connessione al DB
    |
    |-- tests/                        # Suite pytest: pricing, naming, pairing, recommender,
    |                                 #   conservation, levers, API
    |
    |-- db/migration/                 # Migrazioni Flyway, applicate in ordine automaticamente
    |   |-- V1__init_schema.sql       # Schema: wines, quality_predictions, recommendations
    |   |-- V2__seed_wines.sql        # Seed: 6497 vini reali
    |   |-- V3__add_pricing.sql       # Prezzo e margine simulati
    |   |-- V4__add_wine_names.sql    # Nomi descrittivi
    |   |-- V5__add_food_pairing.sql  # Abbinamenti cibo-vino
    |   |-- V6__add_favorites.sql     # Operatori e selezioni di lavoro condivise
    |   |-- V7__add_roles...sql       # Ruoli operativi e profili di mercato
    |   `-- V8__add_logistica_role.sql
    |
    |-- docs/
    |   |-- model_limitations.md      # Limiti noti, quantificati e documentati man mano
    |   `-- knowledge_base/           # Schede sensoriali per il RAG
    |
    |-- models/                       # Modello addestrato (generato da train.py, non versionato)
    |-- data/                         # CSV scaricato da data_loader.py (non versionato, riproducibile)
    |
    |-- Dockerfile                    # Immagine dell'app Streamlit (demo di riserva)
    |-- docker-compose.yml            # Orchestrazione mysql + flyway + backend + frontend
    |-- requirements.txt
    |-- .env.example                  # Template variabili ambiente (DB, chiave LLM)
    `-- .gitignore

## Modello di Machine Learning

Confronto tra 3 algoritmi con 5-fold cross-validation (`compare_models.py`):

| Modello           | RMSE (media) | MAE (media) | R2 (media) |
|--------------------|:---:|:---:|:---:|
| RandomForest       | 0.603 | 0.430 | 0.522 |
| GradientBoosting    | 0.683 | 0.534 | 0.387 |
| LinearRegression    | 0.734 | 0.570 | 0.292 |

RandomForestRegressor scelto per le metriche migliori su tutte e tre le dimensioni.
Modello finale valutato anche su un test set indipendente (20%): RMSE 0.569, R2 0.561.

## Interfaccia

- **Catalogo** (pagina iniziale): griglia con filtri sui parametri chimici, sei
  ordinamenti e paginazione, tutti eseguiti in SQL. Ogni card mostra la bottiglia
  disegnata dai dati, il lotto, il profilo sintetico e il prezzo.
- **Scheda vino** (`/vino/:id`): sidebar per saltare fra le referenze e cinque
  schede contestuali sullo stesso vino — predizione (form precompilato col suo
  profilo), leve di miglioramento, conservazione, raccomandazioni navigabili,
  packaging e SVEVA gia' agganciata al vino.
- **Predizione**: la cantina inserisce **valori di laboratorio propri**, di un
  mosto o di un lotto non ancora a catalogo, e ottiene la stima. Sotto, quali
  variabili guidano davvero la previsione.
- **Conservazione**: il magazzino ordinato per rischio, con i lotti da immettere
  sul mercato per primi in cima.
- **Vendite**: profili di mercato e referenze corrispondenti, ordinate per margine.
- **SVEVA** (Sommelier Virtuale Esperta in Vini e Abbinamenti): domande libere con
  RAG sulla knowledge base enologica.

### Selezioni di lavoro e ruoli

Non esiste registrazione: l'applicazione appartiene a una sola cantina, e chi la
usa si dichiara scegliendo il proprio nome da un elenco che la cantina configura.
Le preferenze sui vini vivono nel database e portano il nome di chi le ha messe,
cosi' un collega vede cosa ha segnato l'altro.

Il ruolo (titolare, enologo, vendite, logistica) determina quali sezioni compaiono
in navigazione. Non e' un sistema di permessi — le altre restano raggiungibili via
URL — ma un modo per mettere davanti a ciascuno gli strumenti del proprio mestiere.

### Guardrail di SVEVA

Il prompt di sistema impone alcuni vincoli espliciti: non inventare vitigni (il
dataset non li contiene), non dichiararsi enologa (e' un titolo professionale che
richiede laurea e albo), citare **un** dato reale a sostegno del consiglio senza
mai menzionare caratteristiche assenti dai dati (tannini, annata, terroir),
valutare onestamente un abbinamento anche quando il vino scelto non e' quello
ideale, e rispondere in due o tre frasi.

Gli input privi di senso sono intercettati da `is_meaningful_question()` **prima**
della chiamata all'LLM: avendo il vino in contesto, il modello tendeva a colmare
il vuoto generando comunque una scheda di degustazione.

## Requisiti della traccia: stato

Fatto: Python 3.11+, OOP (WineRecommender, DatabaseConnection), gestione errori,
GitHub con commit history, Pipeline scikit-learn, valutazione con CV documentata,
persistenza modello con joblib, database MySQL persistente (non CSV),
containerizzazione Docker completa, interfaccia React con API REST FastAPI,
integrazione LLM con prompt engineering, sistema RAG, test automatici (suite
pytest), documentazione dei limiti del modello, spiegabilita' del modello
(importanza per permutazione).

Da fare: dichiarazione etica in forma estesa, slide di presentazione.

## Aspetti etici

**Bias.** Il dataset contiene solo vini portoghesi fermi (Vinho Verde): nessun
rosato, nessuno spumante, nessuna altra regione. Il sistema non fornisce stime per
tipologie fuori da quel dominio. Il modello di embedding usato dal RAG mostra
inoltre un bias culturale documentato sui piatti non occidentali, mitigato con una
knowledge base costruita sulle sensazioni invece che sulle ricette e con ricerca
ibrida semantica piu' lessicale.

**Privacy.** Nessun dato personale nel dataset, che contiene solo misure chimiche
pubbliche. I nomi degli operatori sono etichette di lavoro scelte dalla cantina,
non identita' verificate, e restano sulla sua installazione. I font sono
autoospitati e non da CDN: il browser dell'utente non invia richieste a terzi.

**Trasparenza.** L'interfaccia distingue sempre la natura di cio' che mostra: un
dato misurato, una stima del modello, un valore simulato o un testo generato da un
LLM. Accanto a ogni risultato compaiono le metriche di validazione con i loro
limiti, tenendo distinti R2 in cross-validation (0,52) e su test set (0,56).

**Confini dichiarati.** Dove il dato manca, il sistema lo dice invece di dedurlo:
non nomina vitigni, chiama "conservazione" e non "invecchiamento" un indice che non
puo' vedere i tannini, non usa la menzione "Riserva" perche' indica un affinamento
di cui non c'e' traccia, e non pretende di conoscere le preferenze di un mercato —
le fa dichiarare a chi le conosce.

**Dati simulati.** Prezzo e margine non provengono dal dataset originale, che e'
puramente analitico: sono generati con una logica di business esplicita
(`src/pricing.py`) e dichiarati come tali nell'interfaccia. Non sono listini reali,
e nessuna analisi commerciale viene costruita su di essi come se lo fossero.

**EU AI Act.** Il sistema rientra nella categoria a **rischio minimo**: e' un
supporto decisionale, non prende decisioni autonome o vincolanti e non incide su
diritti delle persone. Le stime accompagnano il giudizio di chi lavora in cantina,
non lo sostituiscono.

## Autore

Marguerite Deido III El Mbimbey - Strumenti AI e Machine Learning con Python.

## Rigenerare i dati da zero

Le migrazioni SQL sono versionate nella repo, quindi `docker compose up` funziona
subito. Se invece vuoi **rigenerare** i dati (es. dopo aver modificato le regole di
pricing o abbinamento), l'ordine e' importante perche' gli script partono dal CSV:

    python src/data_loader.py      # 1. scarica il dataset UCI (crea data/)
    python src/generate_seed.py    # 2. rigenera V2 (seed vini)
    python src/pricing.py          # 3. rigenera V3 (prezzo e margine)
    python src/naming.py           # 4. rigenera V4 (nomi descrittivi)
    python src/pairing.py          # 5. rigenera V5 (abbinamento cibo-vino)
    docker compose down -v && docker compose up --build

Il `down -v` non e' facoltativo: Flyway considera immutabili le migrazioni gia'
applicate e, trovandone una con contenuto diverso, si ferma per checksum non
corrispondente. Conviene inoltre **committare subito** i file rigenerati: sono
generati e non scritti a mano, quindi i piu' esposti a essere sovrascritti per
sbaglio.

Il CSV in `data/` non e' versionato (e' riproducibile scaricandolo di nuovo).

## Documentazione aggiuntiva

- [Limiti del modello e scelte di metodo](docs/model_limitations.md) — raccoglie i
  problemi trovati durante lo sviluppo e come sono stati affrontati: sbilanciamento
  del dataset, bias culturale del modello di embedding, assenza del vitigno, soglie
  di dolcezza portate alla norma UE, menzione "Riserva" rimossa, granularita' degli
  abbinamenti, limiti dell'indice di conservazione e dell'analisi a un fattore per
  volta, spiegabilita' del modello.

## Architettura

L'interfaccia e' stata migrata da Streamlit a un frontend React separato da un
backend FastAPI, che espone come API REST la stessa logica Python gia' esistente
(modello ML, recommender, RAG): nessuna logica di dominio e' stata riscritta, solo
avvolta in un layer HTTP. La versione Streamlit resta disponibile come demo di
riserva e non parte di default.

    Browser  ->  React (nginx, :5174)  ->  FastAPI (:8000)  ->  MySQL (:3306)
                                                            ->  modello joblib
                                                            ->  indice RAG
                                                            ->  OpenRouter (LLM)

Nota: `VITE_API_URL` viene "bruciato" nel bundle statico a build-time, quindi punta
all'indirizzo raggiungibile dal **browser** dell'utente (non dal container).

### Avvio in sviluppo (senza Docker)

```bash
# Backend (terminale 1)
source venv/bin/activate
pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
uvicorn backend.main:app --reload --port 8000

# Frontend (terminale 2)
cd frontend
npm install
npm run dev
```

Il frontend di sviluppo gira su `http://localhost:5173`, il backend su
`http://localhost:8000` (documentazione interattiva su `/docs`).

### Avvio con Docker

```bash
docker compose up -d --build                      # mysql + flyway + backend + frontend
docker compose --profile legacy up -d streamlit   # versione Streamlit, opzionale
```

## Identità del progetto: come si è arrivati al nome

Il nome è **CruScout**, con payoff *Il cruscotto del piccolo produttore*. La
scelta è documentata perché il percorso è passato per tre alternative
scartate, e i motivi dello scarto sono ragionamento di dominio, non gusto.

**"Bacchus"** (prima versione). Coerente con il *Bacco adolescente* di
Caravaggio, allora usato come sfondo del sito, ma molto diffuso nel settore
vino — quindi poco distintivo — e in inglese, mentre l'interfaccia è
interamente in italiano.

**"OXBacco"** (valutata, respinta). L'idea era unire l'esclamazione italiana
a una sigla tecnica, con *OX* a richiamare ossigeno e ossidazione. Scartata
perché **in enologia "ossidato" è un difetto**: un vino ossidato è
maderizzato, deteriorato, e appartiene alla stessa famiglia di problemi
dell'acidità volatile, che in questo dataset è proprio la variabile che
misura il deterioramento. Costruire il marchio su un difetto sarebbe stato
un messaggio contrario a quello del prodotto. In più il gioco di parole non
arrivava: *OXBacco* si legge "oks-bacco", manca il "per", e un nome che va
spiegato non sta funzionando.

**"Oh, per Bacco!"** (valutata, respinta). Conservava l'esclamazione intera
e restava in italiano, ma il registro colloquiale stonava con un prodotto
che si presenta come strumento di analisi. Il tentativo di usare la testa
del sommelier come O iniziale, inoltre, spezzava la parola alla lettura
("icona-h, per Bacco!").

**"CruScout"** regge su due letture sovrapposte:

- *cru* è il termine enologico per la vigna di pregio, e *scout* descrive
  ciò che il sistema fa davvero: esplorare un catalogo e selezionare;
- per un lettore italiano **CruScout suona come "cruscotto"**, il quadro
  strumenti da cui il produttore legge in un colpo d'occhio profilo chimico,
  qualità stimata, prezzo, margine e abbinamenti. In italiano gestionale
  "cruscotto direzionale" è terminologia corrente.

La seconda lettura è quella che governa il payoff, ed è deliberatamente
quella dominante: il dataset **non contiene terroir né origine geografica**,
quindi un nome che promettesse la dimensione del *cru* in senso stretto
prometterebbe ciò che il sistema non può mantenere — lo stesso criterio per
cui il sommelier virtuale non nomina mai i vitigni. *Cru* resta come strato
evocativo, *cruscotto* come promessa operativa.

Il marchio grafico affianca al nome la testa del sommelier virtuale: un
ovale bordato d'oro con tre punti colorati in fila, che legge insieme come
lettera e come tavolozza da pittore. Lo stesso segno è la favicon, dove regge
la lettura anche a 16px, dimensione alla quale la figura intera del sommelier
collasserebbe.

Nota: il nome è scelto per un progetto accademico e non è stato verificato
come marchio registrabile.

### Il Caravaggio: perché è stato rimosso

Il *Bacco adolescente* è stato a lungo lo sfondo del sito, e la scelta di
toglierlo è documentata perché è una decisione di progetto, non un
ripensamento estetico.

È un dipinto **verticale**, mentre il contenuto dell'applicazione è una
colonna centrale su una finestra orizzontale: i due si contendevano lo stesso
spazio. Ogni tentativo di renderlo più visibile — sfondo pieno, fascia
d'apertura, colonna laterale — costava leggibilità al testo o spingeva il
catalogo sotto la piega; ogni tentativo di salvare la leggibilità lo rendeva
invisibile. Con una home diventata catalogo denso, il conflitto non aveva
soluzione: un quadro da museo e una tabella di dati chiedono attenzioni
opposte.

Resta però nell'identità: la **palette bordeaux, crema e oro** del sito è
campionata dai suoi colori, e il progetto ha portato il nome Bacchus prima di
diventare CruScout.

## Nessuna fotografia nel prodotto

Le bottiglie mostrate nel catalogo non sono fotografie ma **disegni generati
dai dati** (`BottleIcon`): il colore del vino deriva da tipo e gradazione, il
livello nella bottiglia dallo zucchero residuo, la capsula dalla qualità. Le
foto di repertorio, provate e poi scartate, mostravano la stessa immagine per
centinaia di referenze diverse — decorazione, non informazione. Un disegno
derivato dai dati, invece, dice qualcosa: due vini con profili diversi
appaiono diversi.

Per lo stesso motivo etichette e astucci restano muti: il dataset non contiene
denominazioni reali, e scriverci sopra un nome sarebbe l'unica invenzione del
progetto.

## Crediti

- Caratteri tipografici: Inter e Righteous, autoospitati via `@fontsource`
- Dataset: Wine Quality (Cortez et al., UCI Machine Learning Repository)
