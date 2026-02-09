# Tvirtebis Platform - Django app
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Logs folder
RUN mkdir -p /app/logs

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ensure python-dotenv and cryptography are installed
RUN pip install --no-cache-dir python-dotenv cryptography

# Copy project files
COPY . .

# Generate .env file before collectstatic
RUN python generate_keys.py

# Tell Django where .env is
ENV DOTENV_PATH=/app/.env

# Collect static files
RUN python manage.py collectstatic --noinput --settings=config.settings

# Expose port
EXPOSE 8000

# Run server
CMD ["gunicorn", "--bind", "0.0.0.0:6048", "--workers", "3", "--timeout", "120", "config.wsgi:application"]

