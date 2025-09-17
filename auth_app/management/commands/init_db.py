from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from video_app.models import Category, Video
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Initialize the database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Initializing database...')
        
        # Create superuser if it doesn't exist
        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write('Creating superuser...')
            User.objects.create_superuser(
                email='admin@videoflix.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('Superuser created'))
        
        # Create sample categories
        categories = ['Drama', 'Comedy', 'Action', 'Horror', 'Romance', 'Sci-Fi']
        for cat_name in categories:
            category, created = Category.objects.get_or_create(name=cat_name)
            if created:
                self.stdout.write(f'Created category: {cat_name}')
        
        self.stdout.write(self.style.SUCCESS('Database initialization complete!'))