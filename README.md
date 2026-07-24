# WineScout Platform

> Trasformare l'istinto del sommelier in algoritmi predittivi grazie al Machine Learning

App Python per piccole cantine artigianali: catalogo vini, predizione qualita (regressione), raccomandazioni content-based (similarita coseno), sommelier virtuale (LLM).

## Stack
Python 3.11+ | Streamlit | MySQL + Flyway | scikit-learn | Docker

## Dataset
Wine Quality Dataset (Cortez et al., UCI ML Repository) - 6497 vini rossi e bianchi.

## Avvio rapido
    pip install -r requirements.txt
    python src/data_loader.py

## Struttura del progetto

    winescout-platform/
    |
    |-- src/                          # Codice applicativo
    |   |-- app.py                    # Entry point Streamlit: catalogo, predizione, raccomandazioni, sommelier
    |   |-- data_loader.py            # Scarica ed unisce Wine Quality Dataset (UCI)
    |   |-- generate_seed.py          # Converte il CSV in seed SQL versionato (V2)
    |   `-- models/
    |       |-- train.py              # Training: Pipeline sklearn (scaler + encoder + RandomForest)
    |       `-- recommender.py        # Classe WineRecommender: raccomandazione con similarita coseno
    |
    |-- db/
    |   `-- migration/                # Migrazioni Flyway, eseguite in ordine automaticamente
    |       |-- V1__init_schema.sql   # Schema: wines, quality_predictions, recommendations
    |       `-- V2__seed_wines.sql    # Seed: 6497 vini reali (1599 rossi, 4898 bianchi)
    |
    |-- models/                       # Modello addestrato (generato, non versionato)
    |   `-- quality_model.pkl
    |
    |-- data/                         # CSV scaricato (non versionato, riproducibile)
    |   `-- wine_quality_merged.csv
    |
    |-- docker-compose.yml            # MySQL con volume persistente + Flyway
    |-- requirements.txt
    |-- .env.example                  # Template variabili ambiente
    |-- .gitignore
    `-- README.md

**Requisiti ancora da completare:**
- Dockerfile per l'app Streamlit (oggi containerizzati solo MySQL e Flyway)
- Dichiarazione etica scritta (bias, GDPR, trasparenza, EU AI Act, limiti)
- Sistema RAG (opzionale, incoraggiato dalla traccia)
- Slide di presentazione
