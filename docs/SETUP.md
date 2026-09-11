# Local Setup

## 1. Clone the repository

```bash
git clone <your-repository-url>
cd OrganizedCompany
```

## 2. Create and activate a virtual environment

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

Create a `.env` file (you can copy from `.env.example`):

```env
SECRET_KEY=change-me
DEBUG=True

# Supported values: sqlite3, postgresql
DB_ENGINE=sqlite3

# PostgreSQL settings (only used when DB_ENGINE=postgresql)
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

## 6. Create a superuser (optional, recommended)

```bash
python manage.py createsuperuser
```

## 7. Run the development server

```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Database Configuration

The project supports two database modes, selected by `DB_ENGINE`:

- `sqlite3` (default): uses the local `db.sqlite3` file
- `postgresql`: reads PostgreSQL credentials from the environment variables above

## Static and Media Files

- Static URL: `/static/`
- Media URL: `/media/`
- Uploaded product images are stored under `media/product_images/`

In development (`DEBUG=True`), static and media routes are served directly by Django.

## Authentication Notes

- Login route: `/users/login/`
- Logout route: `/users/logout/`
- Self-registration is disabled; users are created through admin/staff workflows.

## Running Tests

```bash
python manage.py test
```

Meaningful test coverage currently exists for `sales` (stock-reservation logic), `packing` (scan/complete/partial-ship flow), and `transfers`. Other apps have Django's default test stub only.

## Production Notes

Before deploying:

- Set `DEBUG=False`
- Set a strong, unique `SECRET_KEY`
- Configure `ALLOWED_HOSTS` for your real domain(s)
- Use a production database (PostgreSQL recommended over SQLite)
- Serve static/media via a proper web server or object storage rather than Django's dev file server
- Add security hardening (HTTPS, secure cookies, CSRF/session settings)
