FROM python:3.11-slim
WORKDIR /app
COPY requirements-deploy.txt .
RUN pip install --no-cache-dir -r requirements-deploy.txt
COPY main.py signals.json ./
COPY web ./web
ENV PORT=8080 PYTHONPATH=/app GCP_PROJECT_ID=deploy-sa-lab GCP_LOCATION=us-central1
EXPOSE 8080
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1
