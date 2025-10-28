# Videoflix 

Videoflix is a professional video streaming platform built with Django, allowing users to upload, process, and stream videos with HLS technology. Like Netflix for your own content – automatic multi-resolution streaming from 120p to 1080p.

This project provides a RESTful API with endpoints for:

Authentication & User Management
Video Upload & Streaming
Video Progress Tracking
Category Management
Note: Developed as a portfolio project to demonstrate backend skills in video processing and API development.

## Base URL
After running locally, the API is available at:

http://127.0.0.1:8000/api/

## Getting Started

Clone and set up the project:

```bash
# Clone the repository
git clone https://github.com/HergenEngelhardt/Videoflix.git
cd Videoflix

# Create virtual environment
python -m venv .venv

# Copy environment template
cp .env.template .env
```

### Activate Environment
**Windows:**
```powershell
.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run with Docker (Recommended)
```bash
docker-compose up --build
```

## Troubleshooting: Line Ending Issue
If you see:
```
videoflix_backend | exec ./backend.entrypoint.sh: no such file or directory
```

Make sure `backend.entrypoint.sh` uses LF line endings.

In VS Code: Open file → Bottom-right → Select LF (Unix) → Save.

## Frontend
The matching frontend is available at:
[Videoflix Frontend on GitHub](https://github.com/Developer-Akademie-Backendkurs/project.Videoflix)

## Authentication
Uses JWT token authentication with SimpleJWT.

Include the token in requests:
```
Authorization: Bearer your_jwt_token_here
```

## Permissions
- Authenticated users access video library
- Users manage only their own video progress

## Tech Stack
- Python
- Django & Django REST Framework
- PostgreSQL
- Docker
- Redis
- FFmpeg

Thanks for checking out my Videoflix project!

Happy streaming!