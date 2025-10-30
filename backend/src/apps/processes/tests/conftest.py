import pytest
import uuid

from rest_framework.test import APIClient
from apps.users.models import Profile
from apps.processes.models import Process, ProcessStep
from apps.forms.models import Form


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


@pytest.fixture
def free_process_with_two_steps(db, owner_user):
    from apps.categories.models import ProcessCategory

    owner_profile, _ = Profile.objects.get_or_create(user=owner_user)

    form_a = Form.objects.create(
        name='Free Public',
        access='public',
        password='',
        created_by=owner_user,
        slug=f'fr{uuid.uuid4().hex[:4]}',
    )
    form_b = Form.objects.create(
        name='Free Private',
        access='private',
        password='9999',
        created_by=owner_user,
        slug=f'frp{uuid.uuid4().hex[:4]}',
    )

    proc = Process.objects.create(
        owner=owner_profile,
        title='Free Proc',
        type=Process.FREE_FLOW,
        is_active=True,
    )

    s1 = ProcessStep.objects.create(process=proc, form=form_a, title='Free Step 1', order=1)
    s2 = ProcessStep.objects.create(process=proc, form=form_b, title='Free Step 2', order=2)

    cat = ProcessCategory.objects.create(user=owner_user, name='آزادها')
    cat.process.add(proc)

    return proc, s1, s2, cat