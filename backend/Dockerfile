FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Il contesto di build e' la radice del progetto (vedi docker-compose.yml:
# "context: ." con "dockerfile: backend/Dockerfile"), cosi' possiamo
# copiare requirements.txt, src/, docs/ e models/ che vivono fuori da
# backend/.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu

COPY src/ ./src/
COPY models/ ./models/
COPY docs/ ./docs/
COPY backend/ ./backend/

# Indice RAG costruito durante il build, con la stessa versione di
# chromadb che lo leggera' a runtime (evita il disallineamento visto
# in precedenza con il Dockerfile Streamlit).
RUN python src/rag/build_index.py

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

ENTRYPOINT ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
