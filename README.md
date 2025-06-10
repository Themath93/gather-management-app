# Gather Management App

This project is a simple attendance and group management service built with **FastAPI** and **SQLite**. It provides a REST API used by the bundled frontend pages under `static/`.

## Features

- **User management** – create users, update profile fields and list users with attendance statistics
- **Authentication** – basic email/password login endpoint and JavaScript helpers
- **Group management** – create gatherings and assign attendees into teams automatically
- **Attendance tracking** – record attendance status for each user and meeting
- **Web frontend** – minimal HTML/JS pages for login, the main interface and an admin dashboard

## Project Structure

```
api/                FastAPI routers and endpoints
core/               configuration files (currently empty)
db/                 database session and initialisation scripts
models/             SQLAlchemy model definitions
services/           service layer (placeholder)
static/             frontend HTML, CSS and JS files
tests/              pytest based test suite
main.py             FastAPI application entrypoint
```

## Setup

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio httpx python-multipart
   ```

2. **Initialise the database**

   ```bash
   python db/init_db.py
   # (Optional) populate with sample users
   python db/seed_users.py
   ```

3. **Run the application**

   ```bash
   uvicorn main:app --reload
   ```

   The service will be available at `http://localhost:8000`.  The bundled pages are:

   - `/login` – login form
   - `/` – main page displaying groups and attendance buttons
   - `/admin` – admin dashboard (requires leader/admin role)

## Testing

Tests are located in the `tests/` directory and can be executed with:

```bash
pytest -q
```

They cover authentication and run against an in-memory SQLite database.

## Notes

- The application stores data in `app.db` in the project root when running locally.
- Static files are served from the `static/` directory.

