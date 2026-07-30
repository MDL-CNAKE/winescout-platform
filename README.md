# Bacchus - WineScout AI

> Dagli algoritmi al calice. Senza storie di fantasia.

Applicazione per piccole cantine artigianali: catalogo vini con caratteristiche
chimiche, predizione del punteggio qualita, motore di raccomandazione content-based,
schede packaging e sommelier virtuale basato su LLM con RAG.

Ogni contenuto mostrato deriva dai dati reali del vino (profilo chimico, qualita
misurata, regole enologiche): nessuna descrizione redazionale inventata.

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
    |-- backend/
    |   `-- main.py                   # API FastAPI: /api/wines, /predict, /recommend, /packaging, /sommelier
    |
    |-- frontend/
    |   |-- nginx.conf                # Fallback SPA (try_files): evita il 404 sul refresh delle rotte
    |   `-- src/
    |       |-- api.ts                # Client API tipizzato (axios), unico punto di contatto col backend
    |       |-- router.tsx            # Rotte definite a codice (TanStack Router) + layout condiviso
    |       |-- index.css             # Tema scuro, identita' visiva, layout responsive
    |       |-- components/           # WineCard, Carousel, ChemicalRadar, BottleIcon
    |       `-- routes/
    |           |-- Home.tsx          # Landing: marchio e claim
    |           |-- Catalogo.tsx      # Griglia filtrabile, porta alla scheda del vino
    |           |-- Vino.tsx          # Scheda vino: sidebar + tab predizione/raccomandazioni/packaging/sommelier
    |           |-- Packaging.tsx     # Galleria packaging per stile
    |           `-- Sommelier.tsx     # Sommelier virtuale generico
    |
    |-- src/
    |   |-- app.py                    # Entry point Streamlit (demo di riserva, profilo legacy)
    |   |-- data_loader.py            # Scarica e unisce il Wine Quality Dataset (UCI)
    |   |-- generate_seed.py          # Converte il CSV in seed SQL versionato (V2), con formattazione decimale esplicita
    |   |-- database/
    |   |   `-- connection.py         # DatabaseConnection: context manager, logging, gestione errori
    |   `-- models/
    |       |-- compare_models.py     # Confronto RandomForest/GradientBoosting/LinearRegression con 5-fold CV
    |       |-- train.py              # Training finale: Pipeline sklearn, CV + test set, salvataggio joblib
    |       `-- recommender.py        # WineRecommender: raccomandazione content-based con similarita coseno
    |
    |-- scripts/
    |   `-- test_db_connection.py     # Script di verifica rapida della connessione al DB
    |
    |-- db/migration/                 # Migrazioni Flyway, applicate in ordine automaticamente
    |   |-- V1__init_schema.sql       # Schema: wines, quality_predictions, recommendations
    |   `-- V2__seed_wines.sql        # Seed: 6497 vini reali
    |
    |-- models/                       # Modello addestrato (generato da train.py, non versionato)
    |-- data/                         # CSV scaricato da data_loader.py (non versionato, riproducibile)
    |
    |-- Dockerfile                    # Immagine dell'app Streamlit
    |-- docker-compose.yml            # Orchestrazione mysql + flyway + app
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

- **Home**: identita' del progetto sul Bacco adolescente di Caravaggio (Google Art
  Project, pubblico dominio) e dichiarazione di intenti.
- **Catalogo**: carosello filtrabile per tipo e qualita' minima; ogni card mostra
  foto, numero di lotto e una descrizione generata dai dati chimici reali.
- **Scheda vino** (`/vino/:id`): sidebar per saltare fra i vini e quattro schede
  contestuali sullo stesso vino — predizione (form precompilato col suo profilo,
  per simulare come cambierebbe il punteggio), raccomandazioni (simili e alternative
  piu' economiche, navigabili), packaging, sommelier gia' agganciato al vino.
- **Sommelier virtuale**: domande libere su abbinamenti e degustazione, con RAG
  sulla knowledge base enologica e possibilita' di agganciare un vino del catalogo.

Il sommelier applica alcuni guardrail espliciti nel prompt: non inventa vitigni
(il dataset non li contiene), valuta onestamente gli abbinamenti anche quando il
vino scelto non e' quello ideale, e rifiuta di rispondere a input privi di senso
invece di generare una scheda di degustazione "a compensazione". Quest'ultimo caso
e' intercettato prima della chiamata all'LLM da `is_meaningful_question()`.

## Requisiti della traccia: stato

Fatto: Python 3.11+, OOP (WineRecommender, DatabaseConnection), gestione errori,
GitHub con commit history, Pipeline scikit-learn, valutazione con CV documentata,
persistenza modello con joblib, database MySQL persistente (non CSV), containerizzazione
Docker completa (mysql + flyway + backend + frontend), interfaccia React con API REST
FastAPI, integrazione LLM con prompt engineering per il sommelier, sistema RAG,
test automatici (suite pytest), documentazione dei limiti del modello.

Da fare: dichiarazione etica scritta in forma estesa, slide di presentazione.

## Aspetti etici (sintesi, dettaglio in corso)

- Bias: dataset limitato a vini portoghesi fermi (rossi/bianchi); nessun rosato o
  spumante. Il sistema non fornisce predizioni di qualita per tipologie fuori dal
  dominio di addestramento.
- Privacy: nessun dato personale trattato, solo caratteristiche chimiche pubbliche
  del dataset UCI.
- Trasparenza: l'interfaccia segnala esplicitamente quando una risposta e generata
  da un LLM (sommelier virtuale) e quando e una stima di un modello statistico
  (predizione qualita).
- Limiti: le predizioni sono un supporto decisionale, non sostituiscono il giudizio
  di un sommelier professionista.

 ## - EU AI Act: Il sistema rientra nella categoria di "rischio minimo", in quanto funge da supporto decisionale per l'utente e non prende decisioni autonome o vincolanti.

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

Il CSV in `data/` non e' versionato (e' riproducibile scaricandolo di nuovo).

## Documentazione aggiuntiva

- [Limiti del modello e sbilanciamento dei dati](docs/model_limitations.md)

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

## Crediti immagini

- *Bacco adolescente*, Caravaggio (Google Art Project) - pubblico dominio
- Fotografie di bottiglie e packaging: Unsplash
