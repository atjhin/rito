FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY static/ ./static/
COPY templates/ ./templates/
COPY data/ ./data/
COPY wsgi.py .

EXPOSE 5000

# Prefer gunicorn (recommended on Render)
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-5000} wsgi:app --workers 1 --timeout 600 --graceful-timeout 60"]
