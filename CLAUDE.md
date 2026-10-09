# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
- Activate virtual environment: `source .venv/bin/activate`
- Install dependencies: `uv pip install -r requirements.txt` or `pip install -r requirements.txt`

### Django Management
- Run development server: `python manage.py runserver` (or `.venv/bin/python manage.py runserver`)
- Check project setup: `python manage.py check`
- Create migrations: `python manage.py makemigrations`
- Apply migrations: `python manage.py migrate`
- Create superuser: `python manage.py createsuperuser`
- Django shell: `python manage.py shell`

### Testing
- Run all tests: `python manage.py test`
- Run a specific test app/module: `python manage.py test <app_name>`
- Run a specific test case: `python manage.py test <app_name>.tests.<TestClass>`
- Run a single test method: `python manage.py test <app_name>.tests.<TestClass>.<test_method>`

## Architecture & Project Structure

- **`config/`**: Core project configuration package containing:
  - `settings.py`: Django settings configured to read configuration from `.env` via `python-dotenv`.
  - `urls.py`: Root URL routing configuration.
  - `wsgi.py` / `asgi.py`: WSGI and ASGI entry points for deployment.
- **`manage.py`**: Command-line utility for administrative tasks.
- **`.env`**: Local environment variables (`DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL`).
- **`.env.example`**: Example template for environment configuration.
- **`requirements.txt`**: Python dependencies list.
