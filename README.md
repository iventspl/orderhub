# OrganizedCompany

OrganizedCompany is a Django-based operations platform for managing sales, inventory, warehouses, packing, tracking, customers, staff, and internal collaboration in a multi-company setup.

## Overview

The application is built as a modular monolith with multiple Django apps, each responsible for a business area. It supports:

- Multi-tenant company context via Membership model
- Sales order lifecycle management
- Inventory management with per-warehouse stock and image uploads
- Warehouse and transfer operations
- Packing and tracking workflows
- Customer and contact management
- Staff management with role assignment
- Discussion/help center modules
- REST API endpoints for selected operations

## Tech Stack

- Python 3.12
- Django 6.0.4
- Django REST Framework
- django-storages
- Pillow (image handling)
- python-decouple (environment variables)
- SQLite (default) or PostgreSQL

## Project Structure

Main apps in this repository:

- users: authentication, custom user, company, membership, profile
- mainapp: dashboard/home and shared context processors
- sales: sales orders and order items
- inventory: product catalog, stock, product images
- warehouse: warehouse entities and location logic
- packing: packing workflow
- tracking: shipment tracking
- transfers: stock transfer workflows
- customers: customer records
- contacts: contact management
- reports: reporting features
- staff: staff and assignment management
- discussion: internal discussion features
- helpcenter: support/help center flows
- api: REST endpoints

## Key Concepts

### Multi-Company Access

The platform is scoped by company membership. Most business queries filter by the active user company.

### Inventory Model

Products are unique per SKU and warehouse location (unique constraint). Available quantities are computed across warehouse types (shop/main) and adjusted by reserved quantities.

### Sales Lifecycle

Sales orders include statuses such as Draft, In Warehouse, Packed, Shipped, Delivered, Paid, and Cancelled. Order number generation and order value calculation are handled in model logic.

## API Endpoints

Base path: /api/

- GET /api/sales-orders/
  - Returns sales orders for the authenticated user company
- GET /api/products/search/?q=<query>
  - Returns up to 10 matching products for the authenticated user company

Authentication is required for API endpoints.

## Local Setup

## 1. Clone repository

```bash
git clone <your-repository-url>
cd OrganizedCompany
```

## 2. Create and activate virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure environment variables

Create a .env file (you can copy from .env.example):

```env
SECRET_KEY=change-me
DEBUG=True

# Supported values: sqlite3, postgresql
DB_ENGINE=sqlite3

# PostgreSQL settings
POSTGRES_DB=organizedcompany
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

## 5. Apply migrations

```bash
python manage.py migrate
```

## 6. Create superuser (optional, recommended)

```bash
python manage.py createsuperuser
```

## 7. Run development server

```bash
python manage.py runserver
```

Open: http://127.0.0.1:8000/

## Database Configuration

The project supports two database modes selected by DB_ENGINE:

- sqlite3 (default): uses local db.sqlite3
- postgresql: reads PostgreSQL credentials from environment variables

## Static and Media Files

- Static URL: /static/
- Media URL: /media/
- Uploaded product images are stored under media/product_images/

In development mode, static and media routes are served by Django.

## Authentication Notes

- Login route: /users/login/
- Logout route: /users/logout/
- Self-registration is disabled in routes; users are typically created by admin/staff workflows.

## Running Tests

```bash
python manage.py test
```

## Production Notes

Before production deployment:

- Set DEBUG=False
- Set a strong SECRET_KEY
- Configure ALLOWED_HOSTS
- Configure a production database (PostgreSQL recommended)
- Serve static/media via proper web server or object storage
- Add security hardening (HTTPS, secure cookies, CSRF/session settings)

## License

Copyright (c) 2026 Marek Marczak. All rights reserved.
Proprietary software — unauthorized use, copying, or distribution is prohibited.

## Contributing

Contributions are welcome. Please open an issue or pull request with a clear description of the change.
