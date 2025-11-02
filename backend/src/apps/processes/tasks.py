from datetime import timedelta
from django.utils import timezone
from celery import shared_task
from django.db import transaction
from django.core.cache import cache

from .models import ProcessInstance

@shared_task
def purge_expired_guest_instances():
    now = timezone.now()
    with transaction.atomic():
        qs = ProcessInstance.objects.select_for_update(skip_locked=True).filter(
            started_by__isnull=True,
            access_token__isnull=False,
            access_token_expires_at__lt=now,
        )
        for inst in qs.iterator(chunk_size=500):
            if inst.access_token:
                cache.delete(f'proc:guest:{inst.id}:token')
                cache.delete(f'proc:guest:bytoken:{inst.access_token}')
            inst.delete()