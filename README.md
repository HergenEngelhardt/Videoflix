# Videoflix Backend

A Netflix-like video streaming backend developed with Django REST Framework. The system supports user authentication, HLS video streaming in multiple resolutions, and background video processing.

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

### Option 1: Docker Setup (Recommended)

1. **Clone repository:**
```bash
git clone https://github.com/HergenEngelhardt/Videoflix.git
cd Videoflix
```

2. **Start Docker containers:**
```bash
# Development mode
docker-compose up -d

# Or with build-force
docker-compose up -d --build
```

3. **Check logs:**
```bash
# All services
docker-compose logs -f

# Only web service
docker-compose logs -f web

# Only worker service  
docker-compose logs -f worker
```

4. **Check services:**
```bash
# Status of all containers
docker-compose ps

# Enter container
docker-compose exec web bash
```

5. **Server is available at:** 
- **API:** http://localhost:8000
- **Admin:** http://localhost:8000/admin/
- **RQ Dashboard:** http://localhost:8000/django-rq/

6. **Default login:**
- **Email:** admin@videoflix.com  
- **Password:** admin123

### Production Setup with Docker

1. **Configure environment variables:**
```bash
cp .env.docker.example .env.docker
# Edit .env.docker with your production data
```

2. **Start production containers:**
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

3. **Add SSL certificates (optional):**
```bash
mkdir ssl
# Copy your SSL certificates to the ssl/ folder
```

### Option 2: Local Installation

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

6. **Redis Setup (Optional but recommended):**
```bash
# Windows: https://github.com/microsoftarchive/redis/releases
# Linux: sudo apt-get install redis-server
# Mac: brew install redis
# For local development, change REDIS_HOST=localhost in .env
```

7. **Migrate database:**
```bash
python manage.py migrate
```

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

## Docker Commands

### Development
```bash
# Start containers
docker-compose up -d

# Stop containers
docker-compose down

# Rebuild containers
docker-compose up -d --build

# Container shell
docker-compose exec web bash
docker-compose exec worker bash

# Show logs
docker-compose logs -f web
docker-compose logs -f worker

# Django commands in container
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic
```

### Production
```bash
# Start production containers
docker-compose -f docker-compose.prod.yml up -d --build

# Stop production containers
docker-compose -f docker-compose.prod.yml down

# Production logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Maintenance
```bash
# Delete all containers and volumes (Warning!)
docker-compose down -v
docker system prune -a

# Restart only containers
docker-compose restart web
docker-compose restart worker

# Container resource usage
docker stats
```

### Technologies Used
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

### Code Quality Standards
- PEP 8 compliant
- Functions max. 14 lines
- Snake_case for functions and variables
- PascalCase for classes
- Descriptive variable names
- No unused imports/variables

### Testing
```bash
# Run tests
python manage.py test

# Coverage report
coverage run --source='.' manage.py test
coverage report
```

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