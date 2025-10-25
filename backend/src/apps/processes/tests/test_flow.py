import pytest
from django.urls import reverse
from apps.processes.models import ProcessInstance
from apps.forms.models import Response as FormResponse


def create_response_for_form(form, user=None):
    return FormResponse.objects.create(form=form, user=user)


@pytest.mark.django_db
def test_guest_can_start_and_get_token(api, process_with_two_steps):
    proc, s1, _ = process_with_two_steps
    url = reverse('process-start', kwargs={'pk': proc.pk})

    res = api.post(url)
    assert res.status_code == 201
    assert 'instance' in res.data
    assert 'access_token' in res.data

    instance_id = res.data['instance']['id']
    pi = ProcessInstance.objects.get(pk=instance_id)
    assert pi.started_by is None
    assert pi.current_step_id == s1.id
    assert pi.access_token


@pytest.mark.django_db
def test_current_step_requires_token_for_guest(api, process_with_two_steps):
    proc, s1, _ = process_with_two_steps
    start_url = reverse('process-start', kwargs={'pk': proc.pk})
    res = api.post(start_url)
    assert res.status_code == 201

    instance_id = res.data['instance']['id']
    token = res.data['access_token']

    cur_url = reverse('current-step', kwargs={'pk': instance_id})

    r1 = api.get(cur_url)  # بدون توکن
    assert r1.status_code in (400, 403)

    r2 = api.get(cur_url, {'token': token})
    assert r2.status_code == 200
    assert r2.data['id'] == s1.id


@pytest.mark.django_db
def test_submit_public_then_private_with_password(api, process_with_two_steps):
    proc, s1, s2 = process_with_two_steps
    start_url = reverse('process-start', kwargs={'pk': proc.pk})
    res = api.post(start_url)
    assert res.status_code == 201

    instance_id = res.data['instance']['id']
    token = res.data['access_token']
    submit_url = reverse('submit-step', kwargs={'pk': instance_id})

    fr1 = create_response_for_form(s1.form, user=None)
    r1 = api.post(submit_url, {'form_response': fr1.id, 'token': token})
    assert r1.status_code == 201

    fr2 = create_response_for_form(s2.form, user=None)
    r2 = api.post(submit_url, {'form_response': fr2.id, 'token': token})
    assert r2.status_code in (400, 403)

    r3 = api.post(submit_url, {'form_response': fr2.id, 'token': token, 'password': 'bad'})
    assert r3.status_code in (400, 403)

    r4 = api.post(submit_url, {'form_response': fr2.id, 'token': token, 'password': '1234'})
    assert r4.status_code == 201

    pi = ProcessInstance.objects.get(pk=instance_id)
    assert pi.status == 'completed'
    assert pi.current_step is None