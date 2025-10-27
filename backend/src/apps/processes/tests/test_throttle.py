import pytest
import uuid

from django.urls import reverse
from django.test import override_settings
from apps.users.models import Profile
from apps.forms.models import Form
from apps.processes.models import Process


@pytest.fixture
def simple_process(db, django_user_model):
    owner = django_user_model.objects.create_user(username='own2', password='pass')
    owner_profile, _ = Profile.objects.get_or_create(user=owner)

    form_pub = Form.objects.create(
        name='F',
        access='public',
        password='',
        created_by=owner,
        slug=f'f{uuid.uuid4().hex[:4]}',
    )

    p = Process.objects.create(
        owner=owner_profile,
        title='P',
        type=Process.SEQUENTIAL,
        is_active=True,
    )

    p.steps.create(form=form_pub, title='S', order=1)
    return p


@override_settings(REST_FRAMEWORK={
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.ScopedRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'start_process': '2/minute',
        'current_step': '100/minute',
        'submit_step': '100/minute',
        'user': '100/minute',
        'anon': '100/minute',
    }
})
@pytest.mark.django_db
def test_start_process_throttled_for_guest(api, simple_process):
    url = reverse('process-start', kwargs={'pk': simple_process.pk})
    r1 = api.post(url)
    r2 = api.post(url)
    r3 = api.post(url)

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r3.status_code == 429
    assert 'detail' in r3.data