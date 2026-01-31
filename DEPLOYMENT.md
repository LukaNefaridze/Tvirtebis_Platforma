# Deployment Guide

## Prerequisites

- Python 3.10+
- PostgreSQL 15+
- pip and virtualenv

## Local Development Setup

### 1. Clone and Setup Virtual Environment

```bash
cd d:\TvirtebisPlatforma
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Linux/Mac
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
copy .env.example .env  # On Windows
# cp .env.example .env  # On Linux/Mac
```

Edit `.env` and set:
- `SECRET_KEY` - Generate using: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- `FIELD_ENCRYPTION_KEY` - Generate random 32-byte key
- `DEBUG=True` for development, `False` for production

### 4. Create PostgreSQL Database

```bash
createdb tvirtebis_platform
```

Or using psql:
```sql
CREATE DATABASE tvirtebis_platform;
CREATE USER tvirtebis_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE tvirtebis_platform TO tvirtebis_user;
```

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Setup Initial Data

```bash
python manage.py setup_initial_data
```

This will create:
- Default currencies (GEL, USD, EUR)
- Sample cargo types
- Sample transport types
- Sample volume units
- Superadmin account (you'll be prompted for details)

### 7. Create Static Files Directory

```bash
mkdir static
mkdir logs
```

### 8. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 9. Run Development Server

```bash
python manage.py runserver
```

Access admin panel at: http://localhost:8000/admin/

## Production Deployment

### 1. Update Settings for Production

In `.env`:
```
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
SECRET_KEY=<strong-random-key>
FIELD_ENCRYPTION_KEY=<strong-random-key>
```

### 2. Install Production Server

```bash
pip install gunicorn
```

### 3. Run with Gunicorn

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### 4. Setup Nginx (Example Configuration)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /path/to/TvirtebisPlatforma/staticfiles/;
    }

    location /media/ {
        alias /path/to/TvirtebisPlatforma/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5. Setup SSL with Let's Encrypt

```bash
sudo certbot --nginx -d your-domain.com
```

## Common Management Commands

### Create Admin User
```bash
python manage.py createsuperuser
```

### Run Tests
```bash
python manage.py test
```

### Make Migrations After Model Changes
```bash
python manage.py makemigrations
python manage.py migrate
```

### Clear Cache
```bash
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

## Troubleshooting

### Issue: Database connection error

**Solution**: Check PostgreSQL is running and credentials in `.env` are correct.

```bash
# Check if PostgreSQL is running
pg_isready

# Test connection
psql -U tvirtebis_user -d tvirtebis_platform
```

### Issue: Static files not loading

**Solution**: Run collectstatic and check STATIC_ROOT setting.

```bash
python manage.py collectstatic --clear --noinput
```

### Issue: Encryption field errors

**Solution**: Ensure FIELD_ENCRYPTION_KEY is set in `.env`.

### Issue: Permission denied errors

**Solution**: Check file permissions, especially for media and logs directories.

```bash
chmod -R 755 media/
chmod -R 755 logs/
```

## Backup and Restore

### Backup Database
```bash
pg_dump -U tvirtebis_user tvirtebis_platform > backup.sql
```

### Restore Database
```bash
psql -U tvirtebis_user tvirtebis_platform < backup.sql
```

## Monitoring

### View Logs
```bash
tail -f logs/django.log
```

### Check Running Processes
```bash
ps aux | grep gunicorn
```

## API Testing

### Get Metadata (No Auth)
```bash
curl http://localhost:8000/api/v1/metadata/
```

### List Shipments (With Auth)
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/api/v1/shipments/
```

### Submit Bid
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Transport",
    "price": "250.00",
    "currency": "GEL",
    "estimated_delivery_time": 6,
    "contact_person": "John Doe",
    "contact_phone": "+995555999888"
  }' \
  http://localhost:8000/api/v1/shipments/SHIPMENT_ID/bids/
```
