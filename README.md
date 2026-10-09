# Healthcare Triage

This repository is organized as a Django backend and React frontend.

## Backend (Django)

The existing Django project is in `backend/`.

On its first startup, Django creates `backend/.env` from `.env.example` and
generates a local development secret key. The `.env` file is intentionally
ignored by Git; commit changes meant for other developers to `.env.example`.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver
```

## Frontend (React)

The React application is in `frontend/` and uses Vite.

```bash
cd frontend
npm install
npm run dev
```
