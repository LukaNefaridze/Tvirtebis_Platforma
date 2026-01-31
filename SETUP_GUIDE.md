# Cargo Platform - Setup Guide

## Prerequisites

- Python 3.10+
- PostgreSQL 15+ installed and running
- pip (Python package manager)

## Step-by-Step Setup

### 1. PostgreSQL Setup

#### Option A: Know your PostgreSQL password
If you know your postgres user password, skip to step 2.

#### Option B: Reset PostgreSQL password (Windows)

1. Locate `pg_hba.conf` file (usually in `C:\Program Files\PostgreSQL\[version]\data\`)
2. Open as Administrator
3. Find line with `127.0.0.1/32` and change authentication method to `trust`
4. Restart PostgreSQL service (Services → postgresql-x64-XX → Restart)
5. Open SQL Shell (psql) and connect without password
6. Run: `ALTER USER postgres PASSWORD 'YourNewPassword';`
7. Change `pg_hba.conf` back to `md5` or `scram-sha-256`
8. Restart PostgreSQL service again

#### Create Database

Open SQL Shell (psql) or pgAdmin and run:

```sql
CREATE DATABASE tvirtebis_platform;
```

Or use the provided SQL file:
```bash
psql -U postgres < setup_postgres.sql
```

### 2. Python Environment

Create and activate virtual environment:

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

1. Edit `.env` file in the project root
2. Set your PostgreSQL password:
   ```
   DB_PASSWORD=your_actual_password
   ```

3. Generate secure keys:
   ```bash
   python generate_keys.py
   ```

4. Copy the generated keys to your `.env` file

Your `.env` should look like:
```
SECRET_KEY=django-insecure-a8f7g3h...
DB_NAME=tvirtebis_platform
DB_USER=postgres
DB_PASSWORD=YourActualPassword
DB_HOST=localhost
DB_PORT=5432
FIELD_ENCRYPTION_KEY=a7fH9k2L...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Setup Initial Data

This creates currencies, cargo types, transport types, volume units, and the first superadmin:

```bash
python manage.py setup_initial_data
```

Follow the prompts to create your superadmin account.

### 7. Run Development Server

```bash
python manage.py runserver
```

Access the admin panel at: http://localhost:8000/admin/

## Troubleshooting

### PostgreSQL Connection Failed

**Error:** `FATAL: password authentication failed`

**Solutions:**
1. Verify password in `.env` matches your PostgreSQL password
2. Check PostgreSQL is running: Services → postgresql-x64-XX
3. Verify `DB_HOST=localhost` and `DB_PORT=5432` in `.env`
4. Try connecting with psql: `psql -U postgres -d tvirtebis_platform`

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'apps'`

**Solution:** Make sure you're in the project directory and virtual environment is activated.

### Migration Errors

**Error:** `django.db.utils.OperationalError: database does not exist`

**Solution:** Create the database first:
```sql
CREATE DATABASE tvirtebis_platform;
```

### Encryption Key Error

**Error:** `ImproperlyConfigured: FIELD_ENCRYPTION_KEY`

**Solution:** Generate and set `FIELD_ENCRYPTION_KEY` in `.env`:
```bash
python generate_keys.py
```

## Next Steps

1. Log in to admin panel with your superadmin credentials
2. Add brokers and generate API keys for them
3. Add regular users (cargo owners)
4. Users can create shipments
5. Brokers use API to view shipments and submit bids

## API Documentation

Base URL: `http://localhost:8000/api/v1/`

### Public Endpoints
- `GET /metadata/` - Get dropdown data (no auth)

### Broker Endpoints (require API key)
- `GET /shipments/` - List shipments
- `GET /shipments/{id}/` - Get shipment detail
- `POST /shipments/{id}/bids/` - Submit bid

**Authentication:**
```
Authorization: Bearer {api_key}
```

## Testing

Run tests:
```bash
python manage.py test
```

Run specific test file:
```bash
python manage.py test tests.test_api
python manage.py test tests.test_models
```

## Production Deployment

Before deploying to production:

1. Set `DEBUG=False` in `.env`
2. Update `ALLOWED_HOSTS` with your domain
3. Use strong, unique `SECRET_KEY` and `FIELD_ENCRYPTION_KEY`
4. Use environment-specific `.env` files
5. Set up proper PostgreSQL user (not postgres superuser)
6. Configure HTTPS/SSL
7. Set up gunicorn + nginx
8. Configure static files serving
9. Set up regular database backups

## Support

For issues or questions, refer to:
- Django documentation: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- Django Unfold: https://github.com/unfoldadmin/django-unfold
