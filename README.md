# Cargo Delivery Platform - Backend

Django-based cargo listing platform where admins manage users, users create cargo shipment listings, and external brokers submit bids via REST API.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create PostgreSQL database:
```bash
createdb tvirtebis_platform
```

3. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

4. Generate secret keys:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Setup initial data:
```bash
python manage.py setup_initial_data
```

7. Run development server:
```bash
python manage.py runserver
```

## API Documentation

Base URL: `/api/v1/`

### Endpoints

- `GET /api/v1/metadata/` - Get dropdown data (no auth required)
- `GET /api/v1/shipments/` - List shipments (broker auth required)
- `GET /api/v1/shipments/{id}/` - Get shipment detail (broker auth required)
- `POST /api/v1/shipments/{id}/bids/` - Submit bid (broker auth required)

### Authentication

API requests require Bearer token:
```
Authorization: Bearer {api_key}
```

## Project Structure

- `config/` - Django settings and configuration
- `apps/accounts/` - Admin and User models
- `apps/metadata/` - Dynamic dropdown data (cargo types, etc.)
- `apps/shipments/` - Shipment management
- `apps/bids/` - Bid and broker management
- `apps/api/` - REST API for brokers
