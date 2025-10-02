from django.core.management.base import BaseCommand
import django_rq


class Command(BaseCommand):
    help = 'Test worker functionality and queue status'

    def handle(self, *args, **options):
        try:
            # Test Redis connection
            queue = django_rq.get_queue('default')
            self.stdout.write(f'Connected to Redis queue: {queue}')
            self.stdout.write(f'Queue length: {len(queue)}')
            
            # List failed jobs
            failed_queue = django_rq.get_failed_queue()
            failed_jobs = failed_queue.jobs
            self.stdout.write(f'Failed jobs: {len(failed_jobs)}')
            
            if failed_jobs:
                for job in failed_jobs[:5]:  # Show first 5 failed jobs
                    self.stdout.write(
                        self.style.ERROR(f'Failed job: {job.func_name} - {job.exc_info}')
                    )
            
            # Test simple job
            def test_job():
                return "Worker is working!"
            
            job = queue.enqueue(test_job)
            self.stdout.write(f'Queued test job: {job.id}')
            
            # Check worker status
            workers = django_rq.get_workers()
            self.stdout.write(f'Active workers: {len(workers)}')
            for worker in workers:
                self.stdout.write(f'Worker: {worker.name} - State: {worker.get_state()}')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error testing worker: {str(e)}')
            )