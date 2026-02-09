# Base
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN mkdir -p /app/logs

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install python-dotenv explicitly (settings.py uses it)
RUN pip install --no-cache-dir python-dotenv cryptography

# Copy project files
COPY . .

# Generate .env file (FIELD_ENCRYPTION_KEY + SECRET_KEY)
RUN python generate_keys.py

# Set path so settings.py can find .env
ENV DOTENV_PATH=/app/.env

# Now collectstatic (after .env exists)
RUN python manage.py collectstatic --noinput --settings=config.settings

# Expose port
EXPOSE 8000

# Run command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "config.wsgi:application"]
