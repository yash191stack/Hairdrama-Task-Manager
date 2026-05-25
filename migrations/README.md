# Migrations

Database migration history for Hairdrama Task Manager.

## Locations
- `backend/users/migrations/` - User model migrations
- `backend/tasks/migrations/` - Task model migrations

## Run Migrations
```bash
cd backend
source venv/bin/activate
python manage.py migrate
```

## Create New Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```