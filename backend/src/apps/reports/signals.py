from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.forms.models import Response
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from reports.serializers import FormReportSerializer

@receiver(post_save, sender=Response)
def send_real_time_report(sender, instance, created, **kwargs):
    if created:
        form = instance.form
        serializer = FormReportSerializer(form)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'form_{form.id}_report',
            {
                'type': 'send_report',
                'report': serializer.data
            }
        )
