import pytest
import uuid

from django.urls import reverse
from django.test import override_settings
from apps.users.models import Profile
from apps.forms.models import Form
from apps.processes.models import Process

from apps.processes.views import StartProcessView
from rest_framework.throttling import ScopedRateThrottle


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
    ],
    'DEFAULT_THROTTLE_RATES': {
        'start_process': '2/minute',
    }
})
@pytest.mark.django_db
def test_start_process_throttled_for_guest(api, simple_process):
    StartProcessView.throttle_scope = 'start_process'
    StartProcessView.throttle_classes = [ScopedRateThrottle]

    def _forced_get_throttles(self):
        t = ScopedRateThrottle()
        t.scope = 'start_process'
        return [t]

    StartProcessView.get_throttles = _forced_get_throttles

    url = reverse('process-start', kwargs={'pk': simple_process.pk})

    r1 = api.post(url)
    r2 = api.post(url)
    r3 = api.post(url)

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r3.status_code == 429