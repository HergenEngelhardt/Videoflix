# Videoflix Backend

A Netflix-like video streaming backend developed with Django REST Framework. The system supports user authentication, HLS video streaming in multiple resolutions, and background video processing.

## 📁 Docker Files

- **`backend.Dockerfile`** - Development Dockerfile (Alpine-based, with FFmpeg)
- **`Dockerfile.prod`** - Production Dockerfile (with Gunicorn and security configuration)
- **`backend.entrypoint.sh`** - Startup script for both environments
- **`docker-compose.yml`** - Development setup (with Maildev)
- **`docker-compose.prod.yml`** - Production setup (with Nginx)
- **`.dockerignore`** - Files excluded from Docker container

📖 **Complete Docker Documentation:** See [`DOCKER_SETUP.md`](DOCKER_SETUP.md)

## Features

### Authentication
- User registration with email activation
- Login/Logout with HTTP-Only JWT Cookies
- Token refresh mechanism
- Password reset via email
- Custom User Model with email as username

### Video Management
- Video upload and management via Django Admin
- Automatic HLS conversion in multiple resolutions (120p, 360p, 480p, 720p, 1080p)
- Video categorization
- Thumbnail support
- Background video processing with Redis/RQ

### API Endpoints
- RESTful API according to exact specification
- HLS manifest and segment streaming
- Secure video delivery only for authenticated users
- CORS support for frontend integration

## Quick Start

### ⚠️ IMPORTANT: Create Migrations Before Docker Build!

**Before starting Docker, you must create all migrations locally:**

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

**Reason:** Migrations must exist in the Git repository and are copied into the Docker container. They must NOT be created inside the container.

### Option 1: Docker Setup (Recommended)

**Detailed Guide:** See [`DOCKER_SETUP.md`](DOCKER_SETUP.md)

1. **Clone repository:**
```bash
git clone https://github.com/HergenEngelhardt/Videoflix.git
cd Videoflix
```

2. **Check environment file:**
```bash
# .env file already exists
# Check the most important settings:
# - SECRET_KEY
# - DB_NAME, DB_USER, DB_PASSWORD (must match docker-compose.yml)
# - DJANGO_SUPERUSER_* (for automatic admin creation)
```

3. **Start Docker containers:**
```bash
# Development Mode
docker-compose up -d

# Follow logs
docker-compose logs -f

# Or with force rebuild
docker-compose up -d --build
```

**Important:** The entrypoint script (`backend.entrypoint.sh`) automatically performs:
- Waits for PostgreSQL
- Runs `collectstatic`
- Runs `migrate` (NOT `makemigrations`!)
- Creates superuser (from .env variables)
- Starts RQ Worker in background
- Starts Gunicorn server

**After model changes:**
```bash
# 1. Create migrations LOCALLY
python manage.py makemigrations

# 2. Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

4. **Check services:**
```bash
# Status of all containers
docker-compose ps

# Enter container shell
docker-compose exec web sh

# Logs of individual services
docker-compose logs -f web
docker-compose logs -f worker
docker-compose logs -f db
```

5. **Available services:**
- **API:** http://localhost:8000/api/
- **Admin:** http://localhost:8000/admin/ (Login: see .env DJANGO_SUPERUSER_*)
- **Maildev UI:** http://localhost:1080 (Local inbox for test emails)
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6379

### Option 2: Production Deployment

**See:** [`DOCKER_SETUP.md`](DOCKER_SETUP.md) - Section "Production Deployment"

```bash
# With production compose file
docker-compose -f docker-compose.prod.yml up -d --build

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Option 3: Local Installation (without Docker)

1. **Clone repository:**
```bash
git clone https://github.com/HergenEngelhardt/Videoflix.git
cd Videoflix
```

2. **Create virtual environment:**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt

# Important: Install setuptools if you get import errors
pip install setuptools
```

4. **Configure environment variables:**
For local development, create a `.env` file:
```env
# Django Superuser (will be created automatically)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=your_admin_password
DJANGO_SUPERUSER_EMAIL=admin@yourdomain.com

# Django Settings
SECRET_KEY="your-secret-key-here"
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500

# Database Settings (PostgreSQL - recommended, or leave empty for SQLite)
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432

# For SQLite (local development): Leave DB_* empty or set DB_HOST to empty
# The system will automatically use SQLite if PostgreSQL connection fails

# Redis Settings (for local development change REDIS_HOST to localhost)
REDIS_HOST=localhost
REDIS_LOCATION=redis://localhost:6379/1
REDIS_PORT=6379
REDIS_DB=0

# Email Settings
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email_user
EMAIL_HOST_PASSWORD=your_email_password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=your_email@example.com
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=default_from_email
# Maildev (development mail catcher)
USE_MAILDEV=True
MAILDEV_HOST=localhost
MAILDEV_PORT=1025
DEFAULT_FROM_EMAIL=noreply@videoflix.local
```

**Note:** You can copy and modify the Docker example file for local development:
```bash
cp .env.docker.example .env
# Edit .env with your local settings (change hosts, passwords, etc.)
```

5. **Database Setup:**

**Option A: SQLite (Default - No setup required)**
- For local development, change `DB_HOST=localhost` or leave DB variables empty
- SQLite database will be created automatically

**Option B: PostgreSQL (Recommended for production)**
```bash
# Install PostgreSQL and create database
createdb your_database_name
# Keep DB_HOST=db for Docker, change to localhost for local PostgreSQL
```

**Important for local development:** If you get database connection errors, simply leave the DB_* variables empty in your .env file to use SQLite instead.

6. **Redis Setup (Optional but recommended):**
```bash
# Windows: https://github.com/microsoftarchive/redis/releases
# Linux: sudo apt-get install redis-server
# Mac: brew install redis
# For local development, change REDIS_HOST=localhost in .env
```

7. **Database migrations (IMPORTANT!):**
```bash
# Create new migrations if models changed
python manage.py makemigrations

# Apply migrations to database
python manage.py migrate

# Verify migration status
python manage.py showmigrations
```

**Note:** Always run `makemigrations` first when working with a freshly cloned repository or after pulling changes that modify models. This ensures your database schema matches the current model definitions.

8. **Create superuser:**
```bash
# Automatic creation (if environment variables are set):
python manage.py create_superuser_if_env

# Manual creation (if needed):
python manage.py createsuperuser
```

9. **Create categories:**
```bash
# Go to http://localhost:8000/admin/
# Log in with your superuser  
# Create categories under "Video App" > "Categories"
# Recommended categories: Drama, Comedy, Action, Horror, Romance, Sci-Fi
```

10. **Start server:**
```bash
python manage.py runserver
```

11. **Start RQ Worker (in separate terminal, if Redis is configured):**
```bash
python manage.py rqworker default
```

12. **Check RQ Dashboard (if Redis is configured):**
```bash
# RQ Dashboard: http://localhost:8000/django-rq/
```

## API Documentation

### Authentication Endpoints

#### Registration
```http
POST /api/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "confirmed_password": "securepassword"
}
```

#### Account Activation
```http
GET /api/activate/<uidb64>/<token>/
```

#### Login
```http
POST /api/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

#### Logout
```http
POST /api/logout/
```

#### Token Refresh
```http
POST /api/token/refresh/
```

#### Password Reset
```http
POST /api/password_reset/
Content-Type: application/json

{
  "email": "user@example.com"
}
```

#### Password Confirmation
```http
POST /api/password_confirm/<uidb64>/<token>/
Content-Type: application/json

{
  "new_password": "newsecurepassword",
  "confirm_password": "newsecurepassword"
}
```

### Video Endpoints

#### Video List
```http
GET /api/video/
Authorization: Bearer <token> (or HTTP-Only Cookie)
```

#### HLS Manifest
```http
GET /api/video/<movie_id>/<resolution>/index.m3u8
Authorization: Bearer <token> (or HTTP-Only Cookie)
```

#### HLS Segment
```http
GET /api/video/<movie_id>/<resolution>/<segment>/
Authorization: Bearer <token> (or HTTP-Only Cookie)
```

## Docker Commands (Quick Reference)

**Complete Reference:** See [`DOCKER_SETUP.md`](DOCKER_SETUP.md)

### Container Management
```powershell
# Start
docker-compose up -d

# Stop
docker-compose down

# Rebuild (without cache)
docker-compose build --no-cache

# View logs
docker-compose logs -f web

# Container status
docker-compose ps

# Enter container shell
docker-compose exec web sh
```

### Django Commands in Container
```powershell
# Apply migrations (runs automatically on startup)
docker-compose exec web python manage.py migrate

# Create superuser (if not created automatically)
docker-compose exec web python manage.py createsuperuser

# Django Shell
docker-compose exec web python manage.py shell

# Check migration status
docker-compose exec web python manage.py showmigrations
```

### Troubleshooting
```powershell
# Complete reset
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

# Restart worker
docker-compose restart worker

# Database backup
docker-compose exec db pg_dump -U your_database_user your_database_name > backup.sql
```

## 🐛 Common Problems

### "ValueError: dependency on app with no migrations"
**Solution:** Migrations must be created LOCALLY before Docker build:
```powershell
python manage.py makemigrations
python manage.py makemigrations auth_app
python manage.py makemigrations video_app
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Container won't start / Port conflict
```powershell
# Check ports
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# Kill process
taskkill /PID <PID> /F
```

### More Solutions
See [`DOCKER_SETUP.md`](DOCKER_SETUP.md) - Section "Troubleshooting"

## API Documentation
- **Backend:** Django 5.2.6, Django REST Framework
- **Database:** PostgreSQL (production), SQLite (development)
- **Cache/Queue:** Redis, Django-RQ
- **Authentication:** JWT with HTTP-Only Cookies
- **Video Processing:** FFmpeg for HLS conversion
- **Deployment:** Docker, Docker Compose

### Security Features
- HTTP-Only JWT Cookies (XSS protection)
- Token blacklisting on logout
- CORS configuration
- Secure password validation
- Email activation for new accounts

### Video Processing
- Automatic HLS conversion in background
- Multiple resolutions: 480p, 720p, 1080p
- Adaptive bitrate streaming
- Efficient segment delivery

### Performance Optimizations
- Redis caching
- Background task processing
- Optimized DB queries with select_related
- Static/Media file serving

## Admin Interface

The Django Admin Interface is available at `/admin/` and provides:

- **User Management:** Manage users, activate/deactivate
- **Video Management:** Upload videos, manage categories
- **Monitoring:** Monitor HLS processing status

## Development

### 🔥 IMPORTANT: Best Practices for Model Changes

**For Docker Development:**

Migrations are ALWAYS created locally, NEVER inside the container!

```powershell
# 1. Make model changes in models.py

# 2. Create migrations LOCALLY
python manage.py makemigrations
python manage.py makemigrations auth_app
python manage.py makemigrations video_app

# 3. Commit migrations to Git
git add */migrations/*.py
git commit -m "Add migrations for model changes"

# 4. Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 5. Check logs to verify migrations were applied successfully
docker-compose logs web
```

**Why this is important:**
- ✅ Prevents "dependency on app with no migrations" errors
- ✅ Migration files are copied into Docker image
- ✅ Team members have consistent database schemas
- ✅ `.dockerignore` allows migrations folder (but not `__pycache__`)

**For Local Development (without Docker):**
```bash
# 1. Model-Änderungen in models.py vornehmen
# 2. Migrationen erstellen
python manage.py makemigrations

# 3. Migrationen anwenden
python manage.py migrate

# 4. Server neu starten
python manage.py runserver
```

**Bei Team-Zusammenarbeit:**

**Bei Team-Zusammenarbeit:**
```bash
# Nach Git-Pull mit Model-Änderungen:
# 1. Neue Migrations-Dateien prüfen
git status
git log --oneline

# 2. Migrationen anwenden
python manage.py migrate          # Lokal
# oder
docker-compose exec web python manage.py migrate  # Docker (nur bei bestehenden Migrationen)

# 3. Bei Migrations-Konflikten:
python manage.py showmigrations
```

### Code Quality Standards
- PEP 8 compliant
- Functions max. 14 lines
- Snake_case for functions and variables
- PascalCase for classes
- Descriptive variable names
- No unused imports/variables

### Debugging
- Debug mode in settings.py
- Django Debug Toolbar (optional)
- Logging configuration in settings.py

## Deployment

### Production Setup
1. **Set environment variables:**
   - `DEBUG=False`
   - Secure `SECRET_KEY`
   - Production database
   - Email server configuration

2. **Enable SSL/HTTPS:**
   - Reverse proxy (nginx)
   - SSL certificates
   - Cookie secure flags

3. **Static Files:**
```bash
python manage.py collectstatic
```

4. **Database Migration:**
```bash
python manage.py migrate
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is released under the MIT License. See `LICENSE` file for details.

## Video Processing Pipeline

### HLS Conversion Process
1. **Upload**: Video uploaded via Django Admin
2. **Queue**: Background job queued with Redis/RQ
3. **Processing**: FFmpeg converts to multiple resolutions:
   - 120p (300k bitrate)
   - 360p (800k bitrate)
   - 480p (1200k bitrate)
   - 720p (2500k bitrate)
   - 1080p (5000k bitrate)
4. **Storage**: HLS segments stored in media/hls/
5. **Streaming**: Adaptive bitrate streaming via API

### Performance Optimizations
- Background video processing prevents UI blocking
- HLS adaptive streaming reduces bandwidth usage
- Redis caching for improved response times
- HTTP-Only JWT cookies for security

## Support

For questions or issues:
- GitHub Issues: [https://github.com/HergenEngelhardt/Videoflix/issues](https://github.com/HergenEngelhardt/Videoflix/issues)
- Email: [Your-Email@domain.com](mailto:Your-Email@domain.com)