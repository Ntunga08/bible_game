# Bible Quiz Backend

Bible Quiz Backend is a Django REST Framework project for a Bible trivia game. It handles user accounts, Bible question storage, quiz sessions, daily challenges, scoring, XP, streaks, and leaderboard ranking.

The backend is built for a frontend or mobile app to connect to it. It uses SQLite for local development and JWT authentication for logged-in users.

## Requirements

Install these first:

```txt
Python 3.12+
pip
virtualenv or python -m venv
```

Python packages used by the project:

```txt
Django
djangorestframework
djangorestframework-simplejwt
```

## Start The Project

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

On Windows PowerShell:

```bash
venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install django djangorestframework djangorestframework-simplejwt
```

Create your local environment file:

```bash
cp .env.example .env
```

Apply database migrations:

```bash
python config/manage.py migrate
```

Start the development server:

```bash
python config/manage.py runserver
```

The server will run locally at:

```txt
http://127.0.0.1:8000/
```

## Environment Variables

The local `.env` file is ignored by Git. Put real secrets there and keep `.env.example` safe for sharing.

```txt
DJANGO_SECRET_KEY=required secret key
DJANGO_DEBUG=True or False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_DB_NAME=db.sqlite3
```

## Project Structure

```txt
config/
  manage.py
  config/              Django project settings and root URLs
  apps/
    accounts/          Custom user model, auth, profile, stats
    questions/         Bible categories and quiz questions
    game/              Quiz sessions, answers, scoring, progress
    daily/             Daily challenge attempts
    learderboard/      Player ranking
```

## Useful Commands

Create an admin user:

```bash
python config/manage.py createsuperuser
```

Open the Django admin after starting the server:

```txt
http://127.0.0.1:8000/admin/
```

Run project checks:

```bash
python config/manage.py check
```

Run tests:

```bash
python config/manage.py test apps.accounts apps.questions apps.game apps.daily apps.learderboard
```

## Production Hosting

The Django backend is prepared for Railway or Render.

Install command:

```bash
pip install -r requirements.txt
```

Build command:

```bash
./build.sh
```

Start command:

```bash
cd config && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

Set these environment variables on the hosting provider:

```txt
DJANGO_SECRET_KEY=your-production-secret
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-backend-domain.onrender.com,your-backend-domain.up.railway.app
DATABASE_URL=your-postgres-url
CORS_ALLOWED_ORIGINS=https://your-netlify-site.netlify.app
CSRF_TRUSTED_ORIGINS=https://your-netlify-site.netlify.app
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```
