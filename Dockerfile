# =========================
# Cargo Platform - Django app
# =========================
FROM python:3.11-slim

# =========================
# Environment variables
# =========================
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# =========================
# Set working directory
# =========================
WORKDIR /app

# =========================
# Create logs directory for Django
# =========================
RUN mkdir -p /app/logs

# =========================
# Install system dependencies for psycopg2
# =========================
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# =========================
# Copy requirements and install
# =========================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =========================
# Copy project files
# =========================
COPY . .

# =========================
# Collect static files
# =========================
RUN python manage.py collectstatic --noinput --settings=config.settings

# =========================
# Expose port for Gunicorn
# =========================
EXPOSE 8000

# =========================
# Start Gunicorn
# =========================
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "config.wsgi:application"]
