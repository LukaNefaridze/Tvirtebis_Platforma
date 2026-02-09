# Tvirtebis Platform - Django app
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# სამუშაო ფოლდერი
WORKDIR /app

# შექმენი logs ფოლდერი Django log-ებისთვის
RUN mkdir -p /app/logs

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Static files-ის შეგროვება
RUN python manage.py collectstatic --noinput --settings=config.settings

# Django run port
EXPOSE 8000

# Gunicorn start command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "config.wsgi:application"]
