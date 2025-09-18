#!/bin/bash
set -e

# Function to wait for database
wait_for_db() {
    echo "Waiting for database..."
    while ! nc -z $DATABASE_HOST $DATABASE_PORT; do
        sleep 1
    done
    echo "Database is ready!"
}

# Function to wait for redis
wait_for_redis() {
    echo "Waiting for Redis..."
    while ! nc -z $REDIS_HOST $REDIS_PORT; do
        sleep 1
    done
    echo "Redis is ready!"
}

# Wait for dependencies
if [ "$DATABASE_HOST" ]; then
    wait_for_db
fi

if [ "$REDIS_HOST" ]; then
    wait_for_redis
fi

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
echo "Creating superuser if it doesn't exist..."
python manage.py shell << EOF
import os
from django.contrib.auth import get_user_model
User = get_user_model()

# Get environment variables
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'adminpassword')

if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    print(f'Superuser created: {email} / {username}')
else:
    print('Superuser already exists')
EOF

# Create default categories
echo "Creating default categories..."
python manage.py shell << EOF
from video_app.models import Category
categories = ['Drama', 'Comedy', 'Action', 'Horror', 'Romance', 'Sci-Fi']
for cat_name in categories:
    category, created = Category.objects.get_or_create(name=cat_name)
    if created:
        print(f'Created category: {cat_name}')
EOF

echo "Setup complete!"

# Execute the main command
exec "$@"