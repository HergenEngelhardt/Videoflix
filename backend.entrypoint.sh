#!/bin/sh

set -e

echo "Waiting for PostgreSQL on $DB_HOST:$DB_PORT..."

# -q for "quiet" (no output except errors)
# The loop runs as long as pg_isready is *not* successful (Exit-Code != 0)
while ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -q; do
  echo "PostgreSQL is not reachable - sleeping 1 second"
  sleep 1
done

echo "PostgreSQL is ready - continuing..."

# Original commands (without wait_for_db)
python manage.py collectstatic --noinput

# IMPORTANT: Only migrate, do NOT create migrations in container!
# Migrations must be created locally before building the Docker image.
python manage.py migrate

# Create a superuser using environment variables
# (Your superuser creation code remains the same)
python manage.py shell <<EOF
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'adminpassword')

if not User.objects.filter(username=username).exists():
    print(f"Creating superuser '{username}'...")
    # Correct call: pass username here
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Superuser '{username}' created.")
else:
    print(f"Superuser '{username}' already exists.")
EOF

python manage.py rqworker default &

exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --reload