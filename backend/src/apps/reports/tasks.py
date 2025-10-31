from celery import shared_task
from django.contrib.auth.models import User
from forms.models import Form
from reports.serializers import FormStatsSerializer
from django.core.mail import send_mail
import json

@shared_task
def send_periodic_report():
    admin_users = User.objects.filter(is_superuser=True)

    forms = Form.objects.all()
    report_data = []
    for form in forms:
        stats = FormStatsSerializer(form).data
        report_data.append(stats)

    report_json = json.dumps(report_data, indent=2, ensure_ascii=False)

    for admin in admin_users:
        send_mail(
            subject='Periodic reports of forms',
            message=report_json,
            from_email='no-reply@example.com',
            recipient_list=[admin.email],
            fail_silently=False,
        )

    return f'Report sent to {admin_users.count()} admin(s)'
