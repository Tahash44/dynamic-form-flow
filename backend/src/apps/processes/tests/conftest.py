import pytest
import uuid

from rest_framework.test import APIClient
from django.utils.text import slugify

from apps.users.models import Profile
from apps.processes.models import Process, ProcessStep
from apps.forms.models import Form


def get_profile(user):
    """
    Safely return a Profile for the given user, whether the relation
    is OneToOne or ForeignKey.
    """
    from apps.users.models import Profile

    if hasattr(user, 'profile'):
        return user.profile

    profile = Profile.objects.filter(user=user).first()
    if profile:
        return profile

    return Profile.objects.create(user=user)

@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def owner_user(django_user_model, db):
    user = django_user_model.objects.create_user(username='owner', password='pass')
    Profile.objects.get_or_create(user=user)
    return user


@pytest.fixture
def process_with_two_steps(db, owner_user):
    from apps.forms.models import Form
    from apps.processes.models import Process, ProcessStep
    from apps.users.models import Profile
    import uuid

    owner_profile, _ = Profile.objects.get_or_create(user=owner_user)

    form_pub = Form.objects.create(
        name='Public Form',
        access='public',
        password='',
        created_by=owner_user,
        slug=f'pub{uuid.uuid4().hex[:4]}',
    )
    form_priv = Form.objects.create(
        name='Private Form',
        access='private',
        password='1234',
        created_by=owner_user,
        slug=f'prv{uuid.uuid4().hex[:4]}',
    )

    proc = Process.objects.create(
        owner=owner_profile,
        title='Proc A',
        type=Process.SEQUENTIAL,
        is_active=True,
    )

    step1 = ProcessStep.objects.create(process=proc, form=form_pub, title='Step 1', order=1)
    step2 = ProcessStep.objects.create(process=proc, form=form_priv, title='Step 2', order=2)
    return proc, step1, step2