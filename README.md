# WineScout Platform

> Trasformare l'istinto del sommelier in algoritmi predittivi grazie al Machine Learning

Applicazione Python per piccole cantine artigianali: catalogo vini con caratteristiche
chimiche, predizione del punteggio qualita, motore di raccomandazione content-based
e sommelier virtuale basato su LLM.

Progetto sviluppato per l'esame "Strumenti AI e Machine Learning - Python".

## Stack tecnico

- Python 3.11+, Streamlit (UI)
- MySQL 8.4, migrazioni versionate con Flyway
- scikit-learn (Pipeline, RandomForestRegressor)
- LLM via OpenRouter API (sommelier virtuale, con modalita demo se manca la chiave)
- Docker / docker-compose (mysql + flyway + app)

## Dataset

Wine Quality Dataset di Cortez et al. (UCI ML Repository) - 6497 vini portoghesi
(1599 rossi, 4898 bianchi), 11 feature chimiche + punteggio qualita (3-9).

## Avvio rapido (Docker, consigliato)

Richiede Docker e Docker Compose installati.

    docker compose up --build

Questo comando:
1. avvia MySQL con un volume persistente
2. esegue le migrazioni Flyway (schema + seed di 6497 vini)
3. builda e avvia l'app Streamlit su http://localhost:8501

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

    # avvia l'app
    streamlit run src/app.py

## Struttura del progetto

    winescout-platform/
    |
    |-- src/
    |   |-- app.py                    # Entry point Streamlit: catalogo, predizione, raccomandazioni, sommelier
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

## Requisiti della traccia: stato

Fatto: Python 3.11+, OOP (WineRecommender, DatabaseConnection), gestione errori,
GitHub con commit history, Pipeline scikit-learn, valutazione con CV documentata,
persistenza modello con joblib, database MySQL persistente (non CSV), containerizzazione
Docker completa (app + mysql + flyway), UI Streamlit con 4 sezioni, integrazione LLM
con prompt engineering per il sommelier.

Da fare: dichiarazione etica scritta (bias, GDPR, trasparenza, EU AI Act, limiti),
sistema RAG (opzionale), test automatici, slide di presentazione.

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
