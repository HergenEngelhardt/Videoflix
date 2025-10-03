# Videoflix - Professional Video Streaming Platform! 📺

Hey! This is my video streaming project that I built with Django. It's like Netflix but for your own videos - upload, process, and stream videos with professional HLS streaming technology!

I built this because I wanted to learn how modern video streaming platforms work. The result? A fully-featured platform that automatically converts videos to multiple resolutions and streams them efficiently to any device.

## What can my app do?

✅ **User Management** - Secure registration, login, and profile management  
✅ **Video Upload** - Upload videos in various formats  
✅ **Automatic Processing** - FFmpeg converts videos to HLS streaming format  
✅ **Multi-Resolution Streaming** - 120p to 1080p adaptive streaming  
✅ **Category Management** - Organize videos by categories  
✅ **Thumbnail Generation** - Automatic video thumbnails  
✅ **JWT Authentication** - Secure token-based authentication  
✅ **Email Verification** - Account activation and password reset emails  
✅ **Redis Caching** - Fast performance with Redis  
✅ **Admin Interface** - Full Django admin for content management  
✅ **Responsive API** - RESTful API for frontend integration  

## What I used (my tech stack)

**Backend:** Django 5.2.6 (the framework), Django REST Framework 3.15.2 (for the API)  
**Database:** PostgreSQL (production), SQLite (development)  
**Authentication:** JWT Tokens with SimpleJWT (secure login system)  
**Video Processing:** FFmpeg (converts videos to HLS streaming format)  
**Caching:** Redis (for performance optimization)  
**Task Queue:** Django-RQ with Redis (for background video processing)  
**Image Processing:** Pillow (for thumbnails and image handling)  
**Email:** Django email system (for account verification)  
**Containers:** Docker with Docker Compose (complete development environment)  
**Static Files:** WhiteNoise (for serving static files)  
**Production Server:** Gunicorn (WSGI server)  

## How my streaming works

**HLS (HTTP Live Streaming)** - Industry standard used by Netflix, YouTube  
**Adaptive Bitrate** - Automatically adjusts quality based on connection  
**Multiple Resolutions** - 120p, 360p, 480p, 720p, 1080p  
**Fast Delivery** - Segmented streaming for instant playback  
**Background Processing** - Videos process while users browse  

## What you need to get it running

### If you want to run it with Docker (Recommended!)
- **Docker Desktop** (installed and running)
- **Docker Compose** (comes with Docker Desktop)
- **Git** (to get the code)
- **A web browser**

### If you want to run it locally
- **Python 3.8 or newer**
- **Git** (to get the code)
- **FFmpeg** (for video processing - see installation guide below!)
- **PostgreSQL** (optional, SQLite works for development)
- **Redis** (for caching and task queue)

## Installing FFmpeg (Important for video processing!)

### Windows - Option 1: Download
1. Go to: https://ffmpeg.org/download.html
2. Best to take Windows builds from gyan.dev or BtbN
3. Extract ZIP file to `C:\ffmpeg`
4. Add the path to environment variables:
   - Right-click "This PC" → "Properties" → "Advanced System Settings"
   - "Environment Variables..." → In Path add `C:\ffmpeg\bin`

### Windows - Option 2: Command Line (easier)
```powershell
winget install --id Gyan.FFmpeg -e --source winget
```

### macOS (for Mac users)
Install Homebrew (if not already there):
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
Install FFmpeg:
```bash
brew install ffmpeg
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

**Important:** With Docker you don't need to install FFmpeg yourself - Docker handles everything for you!

## Docker Setup (Recommended! 🐳)

### What you need for Docker
- **Docker Desktop** must be installed and started
- **Docker Compose** (comes with Docker Desktop)

### Docker Desktop Setup
1. Install Docker Desktop from https://www.docker.com/products/docker-desktop/
2. Start Docker Desktop (look for the Docker icon in your taskbar)
3. Test if everything works:
```powershell
docker --version
docker-compose --version
```

**Tip:** Docker Desktop is super handy. You can view containers, read logs, and manage everything. Make sure it's running before you start!

## How to install my project

### 1. Get the code
```bash
git clone https://github.com/HergenEngelhardt/Videoflix.git
cd Videoflix
```

### 2. Set up environment variables
Create a `.env` file in the project root:
```bash
# Copy the example if available, or create new .env file
cp .env.example .env
```

Add the following to your `.env` file:
```env
# Django Superuser (for automatic admin creation)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=adminpassword
DJANGO_SUPERUSER_EMAIL=admin@example.com

# Basic Django settings
SECRET_KEY="django-insecure-lp6h18zq4@z30symy*oz)+hp^uoti48r_ix^qc-m@&yfxd7&hn"
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500

# Database settings for Docker
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=db
DB_PORT=5432

# Redis settings
REDIS_HOST=redis
REDIS_LOCATION=redis://redis:6379/1
REDIS_PORT=6379
REDIS_DB=0

# Email settings (for development - will use console backend)
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email_user
EMAIL_HOST_PASSWORD=your_email_user_password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=default_from_email

# JWT Token settings
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440
```

## Starting the project

### Option 1: With Docker (Recommended! 🚀)

#### First setup with Docker
```powershell
# Make sure Docker Desktop is running!

# Build Docker images
docker-compose build

# Start all services (web app + PostgreSQL + Redis)
docker-compose up -d

# Check if containers are running
docker-compose ps
```

#### Look at Docker Desktop
1. Open Docker Desktop
2. Click on "Containers"
3. You should see your "videoflix" project with three running containers:
   - `videoflix_backend` (Django app)
   - `videoflix_database` (PostgreSQL)
   - `videoflix_redis` (Redis cache)

#### Initial database setup
```powershell
# Run database migrations
docker-compose exec web python manage.py migrate

# Create admin user
docker-compose exec web python manage.py createsuperuser

# Create some test categories (optional)
docker-compose exec web python manage.py shell
```

#### The app will run at:
- **API:** http://127.0.0.1:8000/api/
- **Admin Interface:** http://127.0.0.1:8000/admin/
- **Frontend:** Connect your frontend to the API endpoints

### Option 2: Local development setup

#### 1. Create Python environment
```powershell
python -m venv .venv
.venv\Scripts\activate
```

#### 2. Install dependencies
```powershell
pip install -r requirements.txt
```

#### 3. Set up local database (SQLite)
For local development, you can use SQLite by adding to your `.env`:
```env
# Force SQLite for local development
FORCE_SQLITE=True
```

#### 4. Install and start Redis locally
Download Redis for Windows from: https://github.com/microsoftarchive/redis/releases
Or use Docker just for Redis:
```powershell
docker run -d -p 6379:6379 redis:latest
```

#### 5. Run migrations and create superuser
```powershell
python manage.py migrate
python manage.py createsuperuser
```

#### 6. Start the development server
```powershell
python manage.py runserver
```

## Managing Docker containers

```powershell
# Check container status
docker-compose ps

# View logs
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f redis

# Stop everything
docker-compose down

# Stop and delete database (careful!)
docker-compose down -v

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d

# Access container shell (for debugging)
docker-compose exec web bash
docker-compose exec db psql -U videoflix_user -d videoflix_db
```

## Quick Test Setup

### Test the Docker Setup
```powershell
# Check if containers are running
docker-compose ps

# Test the API
curl http://127.0.0.1:8000/api/

# Test registration
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpassword123"}'
```

### Test Video Upload
After logging in, you can test video upload through the admin interface or API:
1. Go to http://127.0.0.1:8000/admin/
2. Login with your superuser account
3. Add a category in "Video_App > Categories"
4. Upload a video in "Video_App > Videos"
5. The video will be automatically processed to HLS format!

## My API endpoints (for frontend developers)

| URL | Method | What it does | Auth needed? |
|-----|--------|--------------|---------------|
| `/api/register/` | POST | Create new user | No |
| `/api/activate/{uidb64}/{token}/` | GET | Activate user account | No |
| `/api/login/` | POST | Login user | No |
| `/api/logout/` | POST | Logout user | Yes |
| `/api/token/refresh/` | POST | Refresh JWT token | No |
| `/api/password/reset/` | POST | Request password reset | No |
| `/api/password/reset/confirm/` | POST | Confirm password reset | No |
| `/api/categories/` | GET | List all categories | No |
| `/api/videos/` | GET | List all videos | No |
| `/api/videos/{id}/` | GET | Get specific video | No |
| `/api/videos/` | POST | Upload new video | Yes |
| `/api/videos/{id}/` | PUT/PATCH | Update video | Yes |
| `/api/videos/{id}/` | DELETE | Delete video | Yes |

## API Examples

### Create new user
```bash
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword123"}'
```

### Login
```bash
curl -X POST http://127.0.0.1:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword123"}'
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com"
  }
}
```

### Upload video
```bash
curl -X POST http://127.0.0.1:8000/api/videos/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "title=My Video" \
  -F "description=A test video" \
  -F "category=1" \
  -F "video_file=@/path/to/video.mp4"
```

### List videos
```bash
curl -X GET http://127.0.0.1:8000/api/videos/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Video Processing Pipeline

1. **Upload:** User uploads video file
2. **Storage:** Video saved to media directory
3. **Queue:** Processing task added to Redis queue
4. **FFmpeg:** Background worker converts video to HLS
5. **Resolutions:** Multiple qualities generated (120p-1080p)
6. **Thumbnails:** Automatic thumbnail extraction
7. **Ready:** Video available for streaming

## Development Features

### Code Quality
```powershell
# Format code
black .

# Check for issues
flake8 .

# Run tests
pytest

# Run tests with coverage
pytest --cov=.
```

### Database Operations
```powershell
# Create new migration
python manage.py makemigrations

# Apply migrations  
python manage.py migrate

# Django shell
python manage.py shell

# Database shell (PostgreSQL)
python manage.py dbshell
```

### Docker Development
```powershell
# Run migrations in Docker
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

# Run tests in Docker
docker-compose exec web pytest

# Django shell in Docker
docker-compose exec web python manage.py shell
```

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in environment
2. Configure proper PostgreSQL database
3. Set up Redis for production
4. Configure email settings for user verification
5. Set up proper static file serving (nginx)
6. Use Gunicorn as WSGI server
7. Configure SSL/HTTPS
8. Set up monitoring and logging
9. Configure background task workers

### Production Environment Variables
```env
SECRET_KEY=your-production-secret-key
DEBUG=False
DATABASE_URL=postgresql://user:password@localhost/videoflix_db
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
REDIS_URL=redis://localhost:6379/0
EMAIL_HOST=smtp.yourdomain.com
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your-email-password
```

## Troubleshooting

### Common Issues

**FFmpeg not found:**
- Make sure FFmpeg is installed and in your PATH
- With Docker, this is handled automatically

**Video processing fails:**
- Check Redis is running: `docker-compose logs redis`
- Check worker logs: `docker-compose logs web`
- Verify video file format is supported

**Database connection errors:**
- Make sure PostgreSQL container is running: `docker-compose ps`
- Check database logs: `docker-compose logs db`
- Verify environment variables in `.env`

**Permission errors:**
- On Windows: Make sure Docker can access your drive
- On Linux/macOS: Check file permissions

### Debug Mode
Enable debug logging:
```python
# In settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'video_app': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Performance Tips

- Use Redis caching for frequently accessed data
- Optimize video processing with proper FFmpeg settings
- Use CDN for video delivery in production
- Implement pagination for large video lists
- Use database indexing for search functionality
- Consider using background workers for heavy tasks

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/awesome-feature`)
3. Commit your changes (`git commit -m 'Add awesome feature'`)
4. Push to the branch (`git push origin feature/awesome-feature`)
5. Open a Pull Request

## Support

For issues and questions:
- Check this documentation first
- Look at existing issues in the repository  
- Create a new issue with detailed description
- Contact me if needed

## Thanks to

- **Django and DRF communities** for the excellent frameworks
- **FFmpeg developers** for powerful video processing
- **Redis team** for fast caching solutions
- **Docker** for containerization made easy
- **PostgreSQL** for reliable database
- All contributors and testers

## License

This project is open source. Feel free to use it for learning and development!

---

**Thanks for checking out my Videoflix project! 🎬**

Happy streaming! 📺✨