# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production runtime
FROM python:3.12-slim AS runner

WORKDIR /app

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

# Copy installed Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Ensure local bin is on PATH
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy application source and data
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser data/ ./data/
COPY --chown=appuser:appuser api/ ./api/

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
