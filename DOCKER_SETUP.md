# Videoflix Backend - Docker Setup

Dieses Projekt implementiert alle User Stories mit Docker-Unterstützung für Email-Templates und Video-Verarbeitung.

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

```bash
# Kopiere die Beispiel-Umgebungsdatei
cp .env.example .env

# Bearbeite .env mit deinen Einstellungen
nano .env
```

**Wichtige Einstellungen in .env:**

```bash
# Email-Konfiguration (z.B. für Gmail)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

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

### 3. Services überprüfen

```bash
# Worker-Status testen
docker-compose exec web python manage.py test_worker

# Test-Email senden
docker-compose exec web python manage.py test_emails --email test@example.com --type both

# Admin-Interface aufrufen
# http://localhost:8000/admin/
# Credentials: siehe .env (DJANGO_SUPERUSER_*)
```

## Service-Architektur

### Services:
- **web**: Django-Anwendung (Port 8000)
- **worker**: Redis-Worker für Email/Video-Processing  
- **db**: PostgreSQL-Datenbank (Port 5432)
- **redis**: Redis für Queue-Management (Port 6379)

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