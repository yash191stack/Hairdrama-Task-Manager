# Hairdrama Task Manager

A full-stack task management web app where teams can create, assign, and track tasks — with automatic email notifications on key events.

**Live App:** https://frontend-psi-drab-28.vercel.app  
**Backend API:** https://hairdrama-task-manager-production.up.railway.app

---

## What it does

- Sign in with your Google account (no separate signup needed)
- Create tasks with title, description, priority, due date
- Assign tasks to other team members
- Get email notifications when a task is created or marked complete
- Track tasks across two views — ones you created, ones assigned to you

---

## Architecture
                    ┌──────────────────────────┐
                    │      User (Browser)       │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │   Next.js Frontend       │
                    │   TypeScript + Tailwind  │
                    │   Deployed on Vercel     │
                    └────────────┬─────────────┘
                                 │ REST API calls
                                 ▼
                    ┌──────────────────────────┐
                    │   Django Backend         │
                    │   Django REST Framework  │
                    │   Deployed on Railway    │
                    └────┬──────────┬──────────┘
                         │          │
           DB queries    │          │   Email triggers
                         ▼          ▼
          ┌──────────────────┐  ┌──────────────────┐
          │  Supabase        │  │  Gmail SMTP       │
          │  PostgreSQL DB   │  │  Notifications    │
          └──────────────────┘  └──────────────────┘
Auth Flow:
User clicks "Sign in with Google"
→ Google returns access token to frontend
→ Frontend sends token to Django backend
→ Backend verifies with Google API
→ Backend creates/fetches user in Supabase
→ Backend returns JWT token
→ Frontend stores JWT, redirects to dashboard

---

## Tech Stack

| Part | Technology |
|------|------------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS |
| Backend | Django 4.2, Django REST Framework |
| Database | Supabase (PostgreSQL) |
| Authentication | Google OAuth 2.0 + JWT |
| Email | Gmail SMTP |
| Frontend Deploy | Vercel |
| Backend Deploy | Railway |

---

## Project Structure
hairdrama-task-manager/
├── backend/
│   ├── core/                  # Django settings, main urls
│   ├── users/                 # User model, Google OAuth, JWT auth
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── auth_views.py      # Google login endpoint
│   │   ├── auth_service.py    # Token verification logic
│   │   └── urls.py
│   ├── tasks/                 # Task model, CRUD, email triggers
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── email_service.py   # Gmail notification logic
│   │   └── urls.py
│   ├── migrations/            # DB migration docs
│   ├── requirements.txt
│   ├── Procfile
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── login/             # Google OAuth login page
│   │   └── dashboard/         # Main task dashboard
│   ├── components/
│   │   └── tasks/             # TaskCard, CreateTaskModal
│   ├── lib/
│   │   ├── api.ts             # Axios client with JWT interceptors
│   │   ├── auth.ts            # Token helpers
│   │   └── tasks.ts           # Task API functions
│   └── types/                 # TypeScript interfaces
├── migrations/                # Migration history docs
└── README.md

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/users/auth/google/` | Public | Google OAuth login |
| POST | `/api/users/auth/refresh/` | Public | Refresh JWT token |
| GET | `/api/users/profile/` | Required | Get current user |
| PUT | `/api/users/profile/update/` | Required | Update profile |
| GET | `/api/users/list/` | Required | List all users |
| GET | `/api/tasks/` | Required | Get my tasks |
| POST | `/api/tasks/` | Required | Create a task |
| GET | `/api/tasks/:id/` | Required | Get task detail |
| PUT | `/api/tasks/:id/` | Required | Update task |
| DELETE | `/api/tasks/:id/` | Required | Delete task |

---

## Local Setup

### Requirements
- Python 3.9+
- Node.js 18+
- A Supabase project
- Google Cloud Console project with OAuth credentials
- Gmail account with App Password enabled

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in your values
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local      # fill in your values
npm run dev
```

---

## Environment Variables

### Backend (`backend/.env`)
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_PASSWORD=
SUPABASE_URL=
SUPABASE_ANON_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
FRONTEND_URL=http://localhost:3000

### Frontend (`frontend/.env.local`)
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_GOOGLE_CLIENT_ID=

---

## Email Notifications

Two events trigger emails automatically:

1. **Task Created** — the assigned user (or creator if unassigned) gets an email with task details
2. **Task Completed** — the task creator gets notified when status changes to completed

Gmail SMTP is used with an App Password (2FA required on the Gmail account).

---

## Database Migrations

Django migrations are tracked in:
- `backend/users/migrations/` — user model history
- `backend/tasks/migrations/` — task model history

See `/migrations` folder in root for documentation.

To apply migrations fresh:

```bash
cd backend
source venv/bin/activate
python manage.py migrate
```

---

## Deployment (Vercel + Railway)

Already configured: frontend on **Vercel**, backend on **Railway**, DB on **Supabase**.

### 1. Push code (you did this)
```bash
git push origin main
```

### 2. Railway (backend)

Open project → **Variables** → set / update:

| Variable | Example |
|----------|---------|
| `SECRET_KEY` | long random string |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `hairdrama-task-manager-production.up.railway.app,.railway.app` |
| `DATABASE_URL` | `postgresql://...@db.xxx.supabase.co:5432/postgres` |
| `DB_PASSWORD` | same as in Supabase |
| `GOOGLE_CLIENT_ID` | from Google Console |
| `GOOGLE_CLIENT_SECRET` | from Google Console |
| `STABILITY_API_KEY` | your new Stability key |
| `BACKEND_URL` | `https://hairdrama-task-manager-production.up.railway.app` |
| `FRONTEND_URL` | `https://frontend-psi-drab-28.vercel.app` |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | optional |

Then **Deploy** / wait for auto-deploy from `main`.

**Generated images:** saved under `media/` on the server. Add a **Railway Volume** mounted at `/app/media` (or your app root `media`) so images survive redeploys.

### 3. Vercel (frontend)

Project → **Settings → Environment Variables**:

| Variable | Value |
|----------|--------|
| `NEXT_PUBLIC_API_URL` | `https://hairdrama-task-manager-production.up.railway.app/api` |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | same as backend |

Redeploy (or auto from `main`).

### 4. Google OAuth

[Google Cloud Console](https://console.cloud.google.com/) → OAuth client → add:

- **Authorized JavaScript origins:** `https://frontend-psi-drab-28.vercel.app`
- **Authorized redirect URIs:** same + any paths your app uses

### 5. Smoke test

1. Open production frontend → login with Google  
2. Open task → Start → Generate (white / theme / model)  
3. Wait ~30–90s → image appears in gallery  
4. If images 404: check `BACKEND_URL` on Railway and media volume  

### Local vs production

- Never commit `backend/.env` — only set secrets in Railway / Vercel dashboards.  
- After changing API key on Railway, click **Redeploy** (no code change needed if vars only).

