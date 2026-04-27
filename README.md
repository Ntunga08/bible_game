# Bible Quiz Backend

Django REST Framework backend for a Bible quiz game with authentication, question management, game sessions, daily challenges, and leaderboard APIs.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install django djangorestframework djangorestframework-simplejwt
cp .env.example .env
python config/manage.py migrate
python config/manage.py runserver
```

The local `.env` file is ignored by Git. Put real secrets there and keep `.env.example` safe for sharing.

## Environment Variables

```txt
DJANGO_SECRET_KEY=required secret key
DJANGO_DEBUG=True or False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_DB_NAME=db.sqlite3
```

## Main APIs

Auth:

```txt
POST /api/v1/auth/register/
POST /api/v1/auth/login/
POST /api/v1/auth/logout/
POST /api/v1/auth/token/refresh/
GET  /api/v1/auth/me/
GET  /api/v1/auth/me/stats/
POST /api/v1/auth/change-password/
```

Questions:

```txt
GET  /api/v1/categories/
GET  /api/v1/questions/
GET  /api/v1/questions/level/<1-5>/
POST /api/v1/questions/check-answer/
```

Game:

```txt
POST /api/v1/game/start/
GET  /api/v1/game/<session_id>/
GET  /api/v1/game/<session_id>/questions/
POST /api/v1/game/answer/
POST /api/v1/game/<session_id>/complete-level/
POST /api/v1/game/<session_id>/retry/
```

Daily and leaderboard:

```txt
GET  /api/v1/daily/today/
POST /api/v1/daily/answer/
GET  /api/v1/daily/history/
GET  /api/v1/leaderboard/
GET  /api/v1/leaderboard/me/
```

## Checks

```bash
python config/manage.py check
python config/manage.py test apps.accounts apps.questions apps.game apps.daily apps.learderboard
```
