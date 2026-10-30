# Interfaccia Streamlit.
#
# Immagine leggera: l'interfaccia chiede tutto al backend via HTTP, quindi
# non installa torch, chromadb o scikit-learn e non costruisce l'indice RAG
# (lo fa gia' backend/Dockerfile).
FROM python:3.11-slim
WORKDIR /app

# curl serve all'HEALTHCHECK: python:3.11-slim non lo include di default
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-streamlit.txt .
RUN pip install --no-cache-dir -r requirements-streamlit.txt

COPY .streamlit/ ./.streamlit/
COPY src/app.py ./src/app.py
COPY src/ui/ ./src/ui/

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1
ENTRYPOINT ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
