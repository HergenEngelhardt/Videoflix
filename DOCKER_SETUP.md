# Videoflix Backend - Docker Setup & Deployment

Complete guide for Development and Production deployment with Docker.

---

## 📋 Overview

### File Structure
```
Videoflix/
├── backend.Dockerfile           # Development Dockerfile (Alpine-basiert)
├── Dockerfile.prod              # Production Dockerfile (mit Gunicorn)
├── backend.entrypoint.sh        # Startup-Skript für beide Umgebungen
├── docker-compose.yml           # Development Setup
├── docker-compose.prod.yml      # Production Setup
├── .env                         # Environment Variables
└── .dockerignore                # Dateien die nicht in Container kopiert werden
```

### Services
- **db**: PostgreSQL Database
- **redis**: Redis for Queue Management  
- **web**: Django Backend Application
- **worker**: Background Worker for Video Processing & Emails
- **maildev**: (Dev only) Local Mail Server for Testing

---

## 🚀 Quick Start (Development)

### 1. Prerequisites

**Create Local Migrations (CRITICAL!):**

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Create all migrations
python manage.py makemigrations
python manage.py makemigrations auth_app
python manage.py makemigrations video_app

# Verify
python manage.py showmigrations
```

**IMPORTANT:** Migrations must exist LOCALLY BEFORE building the container!

### 2. Environment Setup

Die `.env` Datei ist bereits vorhanden. Überprüfen Sie folgende Werte:

```properties
# Django
SECRET_KEY="your-secret-key-here"
DEBUG=True
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=adminpassword
DJANGO_SUPERUSER_EMAIL=admin@example.com

# Datenbank (muss mit docker-compose.yml übereinstimmen)
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Email (für Development mit Maildev)
USE_MAILDEV=True
MAILDEV_HOST=maildev
MAILDEV_PORT=1025

# Frontend URL
FRONTEND_URL=http://localhost:5500
```

### 3. Docker Container starten

```powershell
# Alle Services starten
docker-compose up -d

# Logs verfolgen
docker-compose logs -f

# Nur bestimmte Services
docker-compose logs -f web
docker-compose logs -f worker
```

### 4. Services überprüfen

```powershell
# Container Status
docker-compose ps

# Admin Interface öffnen
# http://localhost:8000/admin/
# Login: admin / adminpassword (aus .env)

# Maildev UI öffnen (Emails testen)
# http://localhost:1080
```

---

## 🔧 Häufige Befehle

### Container Management

```powershell
# Alle Container stoppen
docker-compose down

# Container + Volumes löschen (kompletter Reset)
docker-compose down -v

# Neu bauen (ohne Cache)
docker-compose build --no-cache

# Neu bauen und starten
docker-compose up --build
```

### Django Commands im Container

```powershell
# Migrationen anwenden
docker-compose exec web python manage.py migrate

# Superuser erstellen (falls nicht automatisch erstellt)
docker-compose exec web python manage.py createsuperuser

# Django Shell
docker-compose exec web python manage.py shell

# Migration Status prüfen
docker-compose exec web python manage.py showmigrations
```

### Datenbank & Redis

```powershell
# PostgreSQL Shell
docker-compose exec db psql -U your_database_user -d your_database_name

# Redis CLI
docker-compose exec redis redis-cli

# Datenbank Backup
docker-compose exec db pg_dump -U your_database_user your_database_name > backup.sql
```

---

## 🐛 Troubleshooting

### Problem: "ValueError: dependency on app with no migrations"

**Ursache:** Migrations-Dateien fehlen im Container.

**Lösung:**
1. Erstellen Sie alle Migrationen LOKAL:
   ```powershell
   python manage.py makemigrations
   python manage.py makemigrations auth_app
   python manage.py makemigrations video_app
   ```

2. Überprüfen Sie, dass Migrations-Dateien existieren:
   ```powershell
   Get-ChildItem .\auth_app\migrations\
   Get-ChildItem .\video_app\migrations\
   ```

3. Container neu bauen:
   ```powershell
   docker-compose down -v
   docker-compose build --no-cache
   docker-compose up
   ```

### Problem: Container startet nicht / Port-Konflikt

```powershell
# Prüfen Sie welche Ports belegt sind
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# Prozess beenden (ersetzen Sie PID mit tatsächlicher Process-ID)
taskkill /PID <PID> /F

# Oder ändern Sie Ports in docker-compose.yml
```

### Problem: Worker verarbeitet keine Videos

```powershell
# Worker Logs prüfen
docker-compose logs worker

# Redis-Verbindung testen
docker-compose exec worker python manage.py shell
>>> import redis
>>> r = redis.Redis(host='redis', port=6379)
>>> r.ping()

# Worker manuell neu starten
docker-compose restart worker
```

### Problem: Emails kommen nicht an

```powershell
# Maildev Logs prüfen
docker-compose logs maildev

# Maildev UI öffnen: http://localhost:1080

# Email im Container testen
docker-compose exec web python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test Message', 'from@test.com', ['to@test.com'])
```

---

## 🏭 Production Deployment

### Production Setup

**1. Environment Variables anpassen:**

Erstellen Sie eine `.env.prod` Datei:

```properties
# Django
SECRET_KEY="GENERATE_NEW_SECRET_KEY_HERE"
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Datenbank
DB_NAME=videoflix_prod
DB_USER=videoflix_user
DB_PASSWORD=STRONG_PASSWORD_HERE
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Email (echte SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Frontend
FRONTEND_URL=https://yourdomain.com
```

**2. Production Container starten:**

```powershell
# Mit .env.prod Datei
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Logs prüfen
docker-compose -f docker-compose.prod.yml logs -f
```

**3. SSL Zertifikate (für Nginx):**

```powershell
# Let's Encrypt Zertifikate erstellen
# Passen Sie nginx.conf entsprechend an
```

---

## 📊 API Endpoints

### Authentication (`/api/`)
- `POST /api/register/` - Benutzerregistrierung
- `POST /api/login/` - Anmeldung (JWT Token)
- `POST /api/logout/` - Abmeldung
- `POST /api/password-reset/` - Passwort zurücksetzen
- `GET /api/activate/{uid}/{token}/` - Account aktivieren

### Videos (`/api/video/`)
- `GET /api/video/` - Alle Videos auflisten
- `POST /api/video/` - Video hochladen
- `GET /api/video/dashboard/` - Dashboard (Hero + Kategorien)
- `GET /api/video/{id}/{resolution}/index.m3u8` - HLS Playlist

### Admin
- URL: `http://localhost:8000/admin/`
- Credentials: Aus `.env` (DJANGO_SUPERUSER_*)

---

## 🎯 Best Practices

### ✅ DO's:
1. **Migrationen LOKAL erstellen** vor Docker-Build
2. **Secrets in .env** niemals committen
3. **Volumes verwenden** für persistente Daten
4. **Logs regelmäßig prüfen**: `docker-compose logs`
5. **Health Checks nutzen** (bereits in docker-compose.yml)
6. **Regelmäßige Backups** der Datenbank erstellen

### ❌ DON'Ts:
1. **NICHT** `makemigrations` im Container ausführen
2. **NICHT** `.env` in Git committen
3. **NICHT** `DEBUG=True` in Production
4. **NICHT** Standard-Passwörter in Production verwenden
5. **NICHT** Port 5432/6379 öffentlich exponieren

---

## 📝 Implementierte Features

### User Stories:
- ✅ **Benutzerregistrierung** mit Email-Aktivierung
- ✅ **Passwort zurücksetzen** via Email
- ✅ **Video-Dashboard** mit Hero-Bereich und Kategorien
- ✅ **Video-Upload** mit automatischer HLS-Konvertierung
- ✅ **Thumbnail-Generierung** aus Videos
- ✅ **Background-Processing** mit Redis Queue

### Worker-Funktionen:
- Email-Versand (Aktivierung & Password-Reset)
- Video-HLS-Konvertierung (mehrere Auflösungen: 360p, 720p, 1080p)
- Thumbnail-Generierung
- Asynchrone Verarbeitung mit RQ (Redis Queue)

---

## 🔍 Monitoring & Debugging

### Container Status

```powershell
# Alle Container
docker-compose ps

# Resource Usage
docker stats

# Container Details
docker inspect videoflix_backend
```

### Logs

```powershell
# Alle Logs
docker-compose logs

# Letzte 100 Zeilen
docker-compose logs --tail=100

# Echtzeit-Logs folgen
docker-compose logs -f web worker

# Seit bestimmter Zeit
docker-compose logs --since 2h
```

### In Container Shell gehen

```powershell
# Web Container
docker-compose exec web sh

# Datenbank Container
docker-compose exec db sh

# Als root
docker-compose exec -u root web sh
```

---

## 📦 Volumes & Daten

### Volumes verwalten

```powershell
# Alle Volumes auflisten
docker volume ls

# Volume inspizieren
docker volume inspect videoflix_postgres_data

# Volume Backup erstellen
docker run --rm -v videoflix_postgres_data:/data -v ${PWD}:/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# Volume wiederherstellen
docker run --rm -v videoflix_postgres_data:/data -v ${PWD}:/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

---

## 🆘 Support

Bei Problemen:
1. Prüfen Sie die Container-Logs: `docker-compose logs -f`
2. Überprüfen Sie `.env` Konfiguration
3. Stellen Sie sicher, dass alle Migrationen existieren
4. Testen Sie Datenbank-Verbindung: `docker-compose exec web python manage.py dbshell`
5. Prüfen Sie Redis: `docker-compose exec redis redis-cli ping`

**Kompletter Reset:**
```powershell
docker-compose down -v
docker system prune -a
docker-compose build --no-cache
docker-compose up
```

---

## 📚 Weitere Informationen

- Django Dokumentation: https://docs.djangoproject.com/
- Docker Dokumentation: https://docs.docker.com/
- Docker Compose: https://docs.docker.com/compose/
- FFmpeg: https://ffmpeg.org/documentation.html
- Redis: https://redis.io/documentation

---

**Version:** 1.0  
**Letzte Aktualisierung:** Oktober 2025

## Implementierte User Stories

### ✅ User Story 1: Benutzerregistrierung
- Registrierungsformular mit E-Mail, Passwort und Passwortbestätigung
- Bestätigungs-E-Mail mit aktivem Link zum Frontend
- Account-Freischaltung erforderlich vor erstem Login
- Sicherheitsfreundliche Fehlermeldungen
- Frontend-Validierung für Pflichtfelder

### ✅ User Story 4: Passwort zurücksetzen  
- "Passwort vergessen"-Funktion
- Sicherheitsfreundliche Rückmeldungen (keine Preisgabe der Kontoexistenz)
- Passwort-Reset-E-Mail mit Frontend-Link
- Responsive E-Mail-Design
- Neues Passwort über E-Mail-Link festlegbar

### ✅ User Story 5: Video-Dashboard
- Hero-Bereich mit hervorgehobenem Video
- Videos nach Genres gruppiert  
- Sortierung nach Erstellungsdatum DESC
- Thumbnails und Titel für jedes Video
- Automatische Thumbnail-Generierung

## Quick Start

### 1. Environment Setup

**⚠️ CRITICAL: Without these steps you'll get AUTH PROBLEMS!**

```bash
# Copy the template file to .env
cp .env.template .env

# Edit .env and set at least the SECRET_KEY
nano .env
```

**REQUIRED - Set SECRET_KEY:**

The `SECRET_KEY` is **mandatory**. Django won't start without it!

```bash
# Generate a new SECRET_KEY:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Copy the output and replace in .env:
SECRET_KEY=paste-generated-key-here
```

**Important settings in .env:**

The `.env.template` already contains working default values for Docker:
- ✅ DB_NAME=videoflix_dev
- ✅ DB_USER=postgres  
- ✅ DB_PASSWORD=postgres
- ✅ DJANGO_SUPERUSER (admin / admin123)

**Only customize if needed:**

# Email-Konfiguration (optional - Maildev wird standardmäßig verwendet)
# Für echte Emails (z.B. Gmail) diese Zeilen aktivieren:
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-password
# DEFAULT_FROM_EMAIL=your-email@gmail.com

# Frontend URL (für Email-Links)
FRONTEND_URL=http://localhost:4200
```

### 2. Docker Compose starten

```bash
# Alle Services starten
docker-compose up -d

# Logs verfolgen
docker-compose logs -f

# Nur bestimmte Services
docker-compose logs -f worker
```

**Note:** The Docker entrypoint script automatically runs migrations on startup. However, if you modify models or pull changes, you should run migrations manually:

```bash
# After model changes - create and apply migrations:
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

# Check migration status:
docker-compose exec web python manage.py showmigrations
```

### 3. Services überprüfen

```bash
# Worker-Status testen
docker-compose exec web python manage.py test_worker

# Test-Email senden
docker-compose exec web python manage.py test_emails --email test@example.com --type both

# Admin-Interface aufrufen
# http://localhost:8000/admin/
# Credentials: siehe .env (DJANGO_SUPERUSER_*)

# Maildev UI öffnen (lokale Mail-Inbox)
# http://localhost:1080
```

## Service-Architektur

### Services:
- **web**: Django-Anwendung (Port 8000)
- **worker**: Redis-Worker für Email/Video-Processing  
- **db**: PostgreSQL-Datenbank (Port 5432)
- **redis**: Redis für Queue-Management (Port 6379)
- **maildev**: Entwicklungs-Mailserver & Inbox (SMTP 1025, Web UI 1080)

### Worker-Funktionen:
- ✅ Email-Versand (Aktivierung & Password-Reset)
- ✅ Video-HLS-Konvertierung (mehrere Auflösungen)
- ✅ Thumbnail-Generierung aus Videos
- ✅ Asynchrone Verarbeitung mit Redis Queue

## API Endpoints

### Authentication:
```
POST /api/register/          # Benutzerregistrierung
POST /api/login/             # Anmeldung  
POST /api/password-reset/    # Passwort-Reset anfordern
POST /api/password-confirm/  # Neues Passwort setzen
GET  /api/activate/{uid}/{token}/  # Account aktivieren
```

### Videos:
```
GET /api/video/              # Alle Videos
GET /api/video/dashboard/    # Dashboard mit Hero + Kategorien
GET /api/video/{id}/{resolution}/index.m3u8  # HLS Playlist
```

### Dashboard Response Format:
```json
{
  "hero_video": {
    "id": 1,
    "title": "Featured Video",
    "description": "...",
    "thumbnail_url": "http://...",
    "category": "Action"
  },
  "categories": {
    "Action": [...],
    "Drama": [...],
    "Comedy": [...]
  }
}
```

## Email-Templates

Templates folgen dem Django-Standard in `auth_app/templates/`:

```
auth_app/templates/
├── static/images/
│   └── logo_videoflix.svg
├── activation_email.html        # HTML-Version
├── activation_email.txt         # Text-Fallback  
├── password_reset_email.html    # HTML-Version
└── password_reset_email.txt     # Text-Fallback
```

**Features:**
- ✅ Responsive Design
- ✅ Django `{% load static %}` für Bilder
- ✅ Frontend-Links mit `FRONTEND_URL`
- ✅ HTML + Text-Versionen

## Troubleshooting

### Worker läuft nicht:
```bash
# Worker-Logs prüfen
docker-compose logs worker

# Redis-Verbindung testen
docker-compose exec worker python manage.py test_worker

# Worker manuell starten
docker-compose exec web python manage.py rqworker default
```

### Emails kommen nicht an:
```bash
# Email-Settings überprüfen
docker-compose exec web python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test', 'from@example.com', ['to@example.com'])

# Entwicklungsmodus: Console Backend
# Emails erscheinen in den Logs statt als echte Emails
```

### Video-Processing Probleme:
```bash
# FFmpeg verfügbar?
docker-compose exec worker ffmpeg -version

# Video-Queue prüfen
docker-compose exec web python manage.py test_worker

# Manuelle Video-Verarbeitung
docker-compose exec web python manage.py shell
>>> from video_app.models import Video
>>> video = Video.objects.first()
>>> from video_app.utils import queue_video_processing
>>> queue_video_processing(video)
```

## Entwicklung

### Neue Abhängigkeiten hinzufügen:
```bash
# Container neu bauen nach requirements.txt Änderungen
docker-compose build
docker-compose up -d
```

### Datenbank-Migrationen:
```bash
# Migrationen erstellen
docker-compose exec web python manage.py makemigrations

# Migrationen anwenden  
docker-compose exec web python manage.py migrate
```

### Logs debuggen:
```bash
# Alle Services
docker-compose logs -f

# Einzelner Service  
docker-compose logs -f web
docker-compose logs -f worker
docker-compose logs -f db
docker-compose logs -f redis
```