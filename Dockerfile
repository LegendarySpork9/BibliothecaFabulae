# Stage 1: Build frontend
FROM node:22-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

COPY Deployments/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY pyproject.toml .
COPY --from=frontend-build /app/frontend/build ./frontend/build

RUN useradd --create-home appuser && \
    mkdir -p /app/data /app/logs && \
    chown -R appuser:appuser /app

USER appuser

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
