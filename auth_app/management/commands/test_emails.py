from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from auth_app.utils import send_activation_email, send_password_reset_email

User = get_user_model()


class Command(BaseCommand):
    help = 'Test email functionality by sending test emails'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email address to send test emails to')
        parser.add_argument('--type', type=str, choices=['activation', 'reset', 'both'], default='both',
                          help='Type of email to send')

    def handle(self, *args, **options):
        email = options['email']
        email_type = options['type']
        
        if not email:
            self.stdout.write(self.style.ERROR('Please provide an email address with --email'))
            return
        
        # Create or get test user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'is_active': False}
        )
        
        if created:
            user.set_password('testpassword123')
            user.save()
            self.stdout.write(f'Created test user: {email}')
        else:
            self.stdout.write(f'Using existing user: {email}')
        
        try:
            if email_type in ['activation', 'both']:
                send_activation_email(user)
                self.stdout.write(
                    self.style.SUCCESS(f'Activation email queued for {email}')
                )
            
            if email_type in ['reset', 'both']:
                send_password_reset_email(user)
                self.stdout.write(
                    self.style.SUCCESS(f'Password reset email queued for {email}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error sending email: {str(e)}')
            )