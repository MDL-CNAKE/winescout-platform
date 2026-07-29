FROM python:3.11-slim
WORKDIR /app

# curl serve all'HEALTHCHECK: python:3.11-slim non lo include di default
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# --extra-index-url punta ai wheel CPU-only di PyTorch: evita di
# scaricare lo stack CUDA (~2.3 GB) inutile senza GPU, l'immagine
# resta di dimensioni ragionevoli.
RUN pip install --no-cache-dir -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu

COPY src/ ./src/
COPY models/ ./models/
COPY docs/ ./docs/

# Costruisce l'indice RAG (ChromaDB) durante il build dell'immagine,
# cosi' e' sempre generato con la stessa versione di chromadb che lo
# leggera' a runtime: nessun disallineamento, nessun passo manuale da
# ricordare dopo un clone o un deploy.
RUN python src/rag/build_index.py

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1
ENTRYPOINT ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
