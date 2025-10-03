# Videoflix - Docker Setup

This is a Docker setup that should facilitate the development and review of the Videoflix project for you and us.

Before using it, please watch the introductory videos at:

[Link to Videos](https://developer-akademie.teachable.com/courses/enrolled/1656501)

## Table of Contents

<!-- TOC -->

- [Videoflix - Docker Setup](#videoflix---docker-setup)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Quickstart](#quickstart)
    - [Setting up and configuring the project](#setting-up-and-configuring-the-project)
      - [Adjusting the settings.py file](#adjusting-the-settingspy-file)
  - [Usage](#usage)
    - [Environment Variables](#environment-variables)
    - [Migrations in Docker Container](#migrations-in-docker-container)
    - [requirements.txt](#requirementstxt)
  - [Troubleshooting](#troubleshooting)

<!-- /TOC -->

---

## Prerequisites

- **Docker** with **docker-compose** installed.

    See [Installation Guide](https://docs.docker.com/compose/install/) for installation.

    Required to start the project as it is fully containerized.

- **git** is installed.

    See [Installation Guide](https://git-scm.com/downloads) for installation.

    Required to download the project.

---

## Quickstart

> [!CAUTION]
> <span style="color: red;">Please follow the instructions described here exactly. If you change the basic
configuration, the project may not start under certain circumstances.</span>
>
> <span style="color: red;">You can change variables in the `.env` file or add new ones. Please do not delete any
of the existing variables.</span>
>
> <span style="color: red;">Please do not change anything about the entries in the `settings.py` specified in the following steps.</span>
>
> <span style="color: red;">Please do not make any changes to the files `backend.Dockerfile`, `docker-compose` and `backend.entrypoint.sh`!<ins></span>
>
> <span style="color: red;">You can (and must) install additional packages and also make corresponding changes to
the `settings.py` file. <ins>Make sure to update your `requirements.txt` file regularly.<ins></span>

1. **Define the environment variables using the [.env.template](./.env.template) file**. Use the
`git bash command line` for this.

    ```bash
    # Creates a .env file with the content of .env.template
    cp .env.template .env
    ```

    > [!IMPORTANT]
    > Make sure that placeholder values are replaced with actual values specific to your environment if necessary.

### Setting up and configuring the project

- Create and activate virtual environment
- Install Django
- Install DRF
- Install django rq
- Install django-redis
- Install gunicorn
- Install psycopg2-binary
- Install python-dotenv
- Install whitenoise
- Update your `requirements.txt` file
- Create the Django project in the current folder
    - project name => core

#### <ins>Adjusting the `settings.py` file

Adjust your `settings.py` file as follows (Please delete unnecessary comments that may only provide you with information for
editing. The ... indicate that there are more lines here, these must also be preserved):

```python
# settings.py

from pathlib import Path
# zwei neue Zeilen
import os
from dotenv import load_dotenv

load_dotenv()
...

# Change the following line
SECRET_KEY = os.getenv('SECRET_KEY', default='django-insecure-@#x5h3zj!g+8g1v@2^b6^9$8&f1r7g$@t3v!p4#=g0r5qzj4m3')

# Add two lines
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", default="localhost").split(",")
CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", default="http://localhost:4200").split(",")

# Add django-rq to your apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_rq', # new line
]

# Add the whitenoise middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # new line
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

...

# Change the database settings and add the configuration for Redis and the RQ-Worker

# Replace the DATABASES setting
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", default="videoflix_db"),
        "USER": os.environ.get("DB_USER", default="videoflix_user"),
        "PASSWORD": os.environ.get("DB_PASSWORD", default="supersecretpassword"),
        "HOST": os.environ.get("DB_HOST", default="db"),
        "PORT": os.environ.get("DB_PORT", default=5432)
    }
}

# Add the configuration for Redis and RQ
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_LOCATION", default="redis://redis:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        },
        "KEY_PREFIX": "videoflix"
    }
}

RQ_QUEUES = {
    'default': {
        'HOST': os.environ.get("REDIS_HOST", default="redis"),
        'PORT': os.environ.get("REDIS_PORT", default=6379),
        'DB': os.environ.get("REDIS_DB", default=0),
        'DEFAULT_TIMEOUT': 900,
        'REDIS_CLIENT_KWARGS': {},
    },
}

...

# Change and extend the configuration for static and media files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

...

```

1. **Build and start the project using `docker-compose`.**

```bash
docker-compose up --build
```

-> if this doesn't work, use (without "-")
```bash
docker compose up --build
```

Open application in browser on [localhost:8000](http://localhost:8000).

---

## Usage

### Environment Variables

All required environment variables are stored in the [.env](./.env) file.

> [!IMPORTANT]
> Please do not change the names of the variables in this configuration. This may result in us
being unable to review and approve the project.
>
> Change existing variables with sensible values if necessary

---

> [!NOTE]
> [backend.entrypoint.sh](backend.entrypoint.sh) automatically creates a superuser based on the
environment variables **`DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD` and `DJANGO_SUPERUSER_EMAIL`**

| Name | Type | Description | Default | Mandatory |
| :--- | :---: | :---------- | :----- | :---: |
| **DJANGO_SUPERUSER_USERNAME** | str | Username for the Django admin superuser account. This user will be automatically created if it doesn't exist. | `admin` |   |
| **DJANGO_SUPERUSER_PASSWORD** | str |  Password for the Django admin superuser account. Make sure it is secure. | `adminpassword` |   |
| **DJANGO_SUPERUSER_EMAIL** | str |  Email address for the Django admin superuser account. Used for account recovery and notifications. | `admin@example.com` |   |
| **SECRET_KEY** | str | A secret key for cryptography in Django. This should be a long, random string and kept confidential. |   | x |
| **DEBUG** | bool | Enables or disables debug mode. Should be set to False in production to prevent exposure of sensitive information. | `True` |   |
| **ALLOWED_HOSTS** | List[str] | A list of strings representing the host/domain names that this Django site can serve. Important for security. | `[localhost]` |   |
| **CSRF_TRUSTED_ORIGINS** | List[str] | Cors-Headers allowed origins. | `[http://localhost:4200]` |   |
| **DB_NAME** | str | Name of the PostgreSQL database to connect to. Important for database operations. | `your_database_name` | x |
| **DB_USER** | str | Username for authentication with the PostgreSQL database. | `your_database_user` | x |
| **DB_PASSWORD** | str | Password for the PostgreSQL database user. | `your_database_password` | x |
| **DB_HOST** | str | Host address of the PostgreSQL database. Usually localhost or the service name in Docker. | `db` |   |
| **DB_PORT** | int | Port number for connecting to the PostgreSQL database. | `5432` |   |
| **REDIS_LOCATION** | str | Redis location | `redis://redis:6379/1` |   |
| **REDIS_HOST** | str | Redis host | `redis` |   |
| **REDIS_PORT** | int | Redis port | `6379` |   |
| **REDIS_DB** | int | Redis DB | `0` |   |
| **EMAIL_HOST** | str | SMTP server address for sending emails. | `smtp.example.com` | x |
| **EMAIL_PORT** | int | Port number for the SMTP server. | `587` |   |
| **EMAIL_USE_TLS** | bool | Enables TLS for email sending. Recommended for security. | `True` |   |
| **EMAIL_USE_SSL** | bool | Email uses SSL | `False` |   |
| **EMAIL_HOST_USER** | str | Username for the email account used to send emails. | `your_email_user` | x |
| **EMAIL_HOST_PASSWORD** | str | Password for the email account. Pay attention to security. | `your_email_password` | x |
| **DEFAULT_FROM_EMAIL** | str | Email address used by Django | `EMAIL_HOST_USER` |   |

### Migrations in Docker Container

To transfer changes made to the database structure to Docker, you have two different options:

1. Completely recreate Docker container (not recommended)

    - Stop Docker in the command line with the key combination `Ctrl+C`
    - Restart Docker with the command `docker-compose up --build`
    - If `docker-compose up --build` doesn't work, use `docker compose up --build`

2. Execute the migration directly in the Docker container (better)

    - Create the migration files directly in the Docker container

    ```bash
    docker-compose exec web python manage.py makemigrations
    ```

    This command is executed directly in the bash of the Docker container. (We remember, our Docker setup
    basically contains a complete operating system)

    - Execute the migration:

    ```bash
    docker-compose exec web python manage.py migrate
    ```

### requirements.txt

The dependencies of the application are listed in the [requirements.txt](./requirements.txt) file.

To change them in the Docker container, the application must be rebuilt.

To list only the primary (top-level) packages that you installed via `pip` - without showing their dependencies
- use:

```bash
pip list --not-required
```

## Troubleshooting

- **When starting Docker I get this error in the command line:**

    ```bash
    unable to get image 'postgres:latest': error during connect:
    Get "http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/v1.48/images/postgres:latest/json":
    open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
    ```

    > [!NOTE]
    > Please make sure you have started Docker Desktop.

- **Starting Docker aborts with the following message in the console:**

    ```bash
    videoflix_backend   | exec ./backend.entrypoint.sh: no such file or directory
    videoflix_backend exited with code 255
    ```

    > [!NOTE]
    > Please make sure that the `backend.entrypoint.sh` file is saved with the End of Line Sequence LF.
    >
    > See [Google Search](https://www.google.com/search?sca_esv=81208bf63503b115&rlz=1C1CHBF_deDE1069DE1069&q=cr+lf+lf+in+vscode&spell=1&sa=X&ved=2ahUKEwihofbto4eNAxXK9bsIHXhtCLYQBSgAegQIDxAB&biw=1920&bih=911&dpr=1)

- **When starting the Docker container you get an error message after changing the database that the
database migration fails.**

    > [!NOTE]
    > This can happen if you make changes to a model. To still be able to perform a migration
    you can use the following command:
    >
    > ```bash
    > # docker run --rm [OPTIONS] <YOUR_IMAGE_NAME> <YOUR_MIGRATION_COMMAND>
    > docker run --rm web python manage.py makemigrations
    >
    > # Often this command alone is enough to bypass the problem at the next start.
    > # For safety, you can also directly perform the actual migration afterwards.
    > docker run --rm web python manage.py migrate
    > ```
    >
---
