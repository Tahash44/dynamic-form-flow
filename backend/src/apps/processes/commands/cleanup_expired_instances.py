from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.processes.models import ProcessInstance

class BaseCommand(BaseCommand):
    help = 'Cleanup expired guest instances'

    def handle(self, *args, **options):
        now = timezone.now()
        qs = ProcessInstance.objects.filter(
            started_by__isnull=True,
            access_token_expires_at__lt=now,
            status='running'
        )
        updated = qs.update(status='aborted')
        self.stdout.write(self.style.SUCCESS(f'Aborted {updated} expired guest instances'))