# OrganizedCompany

A Django-based, multi-tenant operations platform for a small logistics/retail business — covering sales orders, multi-warehouse inventory, barcode-scanning packing, shipment tracking, customers, and staff, all scoped per company.

<!-- Drop screenshots or a short GIF walkthrough in docs/images/ and reference them here, e.g.: -->
<!-- ![Packing screen](docs/images/packing-screen.png) -->

## Highlights

- **Multi-tenant by design** — every business object is scoped to a `Company` through a `Membership` model; one user can belong to one company
- **Atomic multi-warehouse stock reservation engine** — reserves from an employee's assigned warehouse first, overflows to the central warehouse, and stays correct under concurrent orders via row locking and `F()`-expression updates ([details](docs/FEATURES.md#multi-warehouse-stock-reservation-engine))
- **Mobile camera barcode scanning** for packing, with a live progress bar, manual +/- fallback, and a full per-scan audit trail
- **Partial shipment / backorder handling** — ship what's ready, auto-generate a backorder for the rest
- **PDF packing lists** generated on demand (ReportLab, Unicode-safe for Polish text)
- **REST API** for order data and product typeahead search (Django REST Framework)
- See [docs/ENGINEERING_HIGHLIGHTS.md](docs/ENGINEERING_HIGHLIGHTS.md) for real concurrency/Django-internals bugs found and fixed while building the reservation engine

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | Python 3.12, Django 6.0.4 |
| API | Django REST Framework |
| Database | SQLite (default) or PostgreSQL |
| Frontend | Server-rendered Django templates, hand-written vanilla JS/CSS (no SPA framework) |
| Barcode scanning | [html5-qrcode](https://github.com/mebjas/html5-qrcode) (client-side, device camera) |
| PDF generation | ReportLab |
| Config | python-decouple (.env-based settings) |

## Project Structure

One Django project (`core`) with ~14 apps, each owning a business domain — see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full app map, data model, and multi-tenancy design.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — app map, data model, multi-tenancy, order lifecycle
- [Features](docs/FEATURES.md) — deep-dives into the packing/scanning workflow, reservation engine, and backorder flow
- [Engineering Highlights](docs/ENGINEERING_HIGHLIGHTS.md) — real concurrency and Django-signal bugs found and fixed
- [API Reference](docs/API.md) — REST endpoints with example requests/responses
- [Setup Guide](docs/SETUP.md) — full local installation and configuration steps

## Quick Start

```bash
git clone <your-repository-url> && cd OrganizedCompany
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit as needed
python manage.py migrate
python manage.py runserver
```

Full walkthrough, environment variables, and production notes: [docs/SETUP.md](docs/SETUP.md).

## License

Copyright (c) 2026 Marek Marczak. All rights reserved.
Proprietary software — unauthorized use, copying, or distribution is prohibited.

## Contributing

Contributions are welcome. Please open an issue or pull request with a clear description of the change.
