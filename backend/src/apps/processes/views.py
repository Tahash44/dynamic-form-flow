import secrets
from datetime import timedelta

from django.db.models import Prefetch
from django.utils import timezone
from rest_framework import status, filters
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, ListCreateAPIView, \
    RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from .models import Process, ProcessInstance, ProcessStep, StepSubmission
from .permissions import IsOwnerOrReadOnly
from .serializers import ProcessSerializer, ProcessStepSerializer, ProcessInstanceSerializer, StepSubmissionSerializer, \
    ProcessWriteSerializer, ProcessStepWriteSerializer, FreeStepSerializer, StepWithFormSerializer
from ..forms.models import Field
from apps.forms.models import Response as FormResponse, Answer as FormAnswer, Field as FormField
from django.core.cache import cache


def get_form_password_from_request(request):
    return (
        request.data.get('password')
        or request.headers.get('X-Form-Password')
        or request.query_params.get('password')
    )


def ensure_form_password_if_private(form, request):
    if getattr(form, 'access', 'public') != 'private':
        return
    provided = get_form_password_from_request(request)
    real = getattr(form, 'password', '') or ''
    if provided != real:
        raise ValidationError({'detail': 'Form is private. Password required or incorrect.'})


def get_instance_token_from_request(request):
    return (
        request.headers.get('X-Instance-Token')
        or request.query_params.get('token')
        or request.data.get('token')
    )


def require_guest_token_if_needed(request, instance):
    if instance.started_by_id:
        return
    token = (
        request.headers.get('X-Instance-Token')
        or request.query_params.get('token')
        or request.data.get('token')
    )
    if not token:
        raise ValidationError({'detail': 'Guest instance token is required.'})

    cached = cache.get(f'proc:guest:{instance.id}:token')
    if cached is None:
        if token != (instance.access_token or ''):
            raise ValidationError({'detail': 'Invalid guest token.'})
        if instance.access_token_expires_at and timezone.now() > instance.access_token_expires_at:
            raise ValidationError({'detail': 'Guest token expired.'})
    else:
        if token != cached:
            raise ValidationError({'detail': 'Invalid guest token.'})

def build_form_response_from_answers_or_skip(step_form, request):
    skip = bool(request.data.get('skip', False))
    if skip:
        return FormResponse.objects.create(
            form=step_form,
            user=request.user if request.user.is_authenticated else None
        )

    answers_payload = request.data.get('answers')
    if not isinstance(answers_payload, list) or not answers_payload:
        raise ValidationError({'detail': 'answers must be a non-empty list or use skip=true.'})

    field_ids = [a.get('field') for a in answers_payload]
    if not all(isinstance(fid, int) for fid in field_ids):
        raise ValidationError({'detail': 'each answer.field must be integer id.'})

    fields_qs = FormField.objects.filter(form=step_form, id__in=field_ids)
    if fields_qs.count() != len(set(field_ids)):
        raise ValidationError({'detail': 'some fields do not belong to current form.'})

    fr = FormResponse.objects.create(
        form=step_form,
        user=request.user if request.user.is_authenticated else None
    )
    FormAnswer.objects.bulk_create([
        FormAnswer(response=fr, field_id=a['field'], value=str(a.get('value', '')).strip())
        for a in answers_payload
    ])
    return fr


class ProcessListView(ListAPIView):
    queryset = Process.objects.filter(is_active=True)
    serializer_class = ProcessSerializer
    permission_classes = [AllowAny]


class ProcessSequentialListView(ListAPIView):
    queryset = Process.objects.filter(is_active=True, type=Process.SEQUENTIAL)
    serializer_class = ProcessSerializer
    permission_classes = [AllowAny]


class ProcessFreeListView(ListAPIView):
    queryset = Process.objects.filter(is_active=True, type=Process.FREE_FLOW)
    serializer_class = ProcessSerializer
    permission_classes = [AllowAny]


class StartProcessView(CreateAPIView):
    serializer_class = ProcessInstanceSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        try:
            process = Process.objects.get(pk=pk, is_active=True, type=Process.SEQUENTIAL)
        except Process.DoesNotExist:
            raise ValidationError({'detail': 'Process not found or inactive.'})

        access_token = None

        if not request.user.is_authenticated:
            ttl_hours = 48
            ttl_seconds = ttl_hours * 3600
            token = secrets.token_urlsafe(48)
            expires = timezone.now() + timedelta(hours=ttl_hours)

            instance = ProcessInstance.objects.create(
                process=process,
                started_by=None,
                access_token=token,
                access_token_expires_at=expires,

            )
            cache.set(f'proc:guest:{instance.id}:token', token, timeout=ttl_seconds)
            cache.set(f'proc:guest:bytoken:{token}', instance.id, timeout=ttl_seconds)

            access_token = token

        else:
            instance = ProcessInstance.objects.create(
                process=process,
                started_by=request.user,
                access_token=None,
                access_token_expires_at=None,
            )

        instance.start()

        data = self.get_serializer(instance).data
        return Response(
            {'instance': data, 'access_token': access_token} if access_token else data,
            status=status.HTTP_201_CREATED
        )


class CurrentStepView(RetrieveAPIView):
    queryset = (ProcessInstance.objects.select_related('current_step__form', 'process').prefetch_related(Prefetch('current_step__form__fields', queryset=Field.objects.order_by('position'))))
    serializer_class = StepWithFormSerializer
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        require_guest_token_if_needed(request, instance)

        step = instance.current_step
        if not step:
            return Response({'detail': 'Process completed.'})

        ensure_form_password_if_private(step.form, request)
        return Response(self.get_serializer(step).data)


class SubmitStepView(CreateAPIView):
    serializer_class = StepSubmissionSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        instance = ProcessInstance.objects.select_related('current_step__form', 'process').filter(
            pk=self.kwargs.get('pk')
        ).first()
        if not instance:
            raise ValidationError({'detail': 'Instance not found.'})

        require_guest_token_if_needed(request, instance)

        step = instance.current_step
        if not step:
            raise ValidationError({'detail': 'Process already completed.'})

        ensure_form_password_if_private(step.form, request)

        fr = build_form_response_from_answers_or_skip(step.form, request)

        payload = {'instance': instance.id, 'step': step.id, 'form_response': fr.id}
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        instance.refresh_from_db()
        instance.advance_after_submission(step)

        return Response(ProcessInstanceSerializer(instance).data, status=status.HTTP_201_CREATED)


class ProcessListCreateView(ListCreateAPIView):
    queryset = Process.objects.filter(type=Process.SEQUENTIAL)
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['created_at', 'title']

    def get_serializer_class(self):
        return ProcessWriteSerializer if self.request.method == 'POST' else ProcessSerializer

    def get_queryset(self):
        return super().get_queryset().filter(owner__user=self.request.user)


class ProcessRUDView(RetrieveUpdateDestroyAPIView):
    queryset = Process.objects.filter(type=Process.SEQUENTIAL)
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_serializer_class(self):
        return ProcessWriteSerializer if self.request.method in ('PUT', 'PATCH') else ProcessSerializer


class StepListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return ProcessStep.objects.filter(process_id=self.kwargs['process_id']).select_related('process')

    def get_serializer_class(self):
        return ProcessStepWriteSerializer if self.request.method == 'POST' else ProcessStepSerializer

    def perform_create(self, serializer):
        process = Process.objects.get(pk=self.kwargs['process_id'], type=Process.SEQUENTIAL)
        self.check_object_permissions(self.request, process)
        serializer.save(process=process)


class StepRUDView(RetrieveUpdateDestroyAPIView):
    queryset = ProcessStep.objects.select_related('process')
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_serializer_class(self):
        return ProcessStepWriteSerializer if self.request.method in ('PUT', 'PATCH') else ProcessStepSerializer
    

class StartFreeProcessView(CreateAPIView):
    serializer_class = ProcessInstanceSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        try:
            process = Process.objects.get(pk=pk, is_active=True, type=Process.FREE_FLOW)
        except Process.DoesNotExist:
            raise ValidationError({'detail': 'Process not found or inactive.'})

        if request.user.is_authenticated:
            existing = ProcessInstance.objects.filter(
                process=process, started_by=request.user, status='running'
            ).first()
            if existing:
                raise ValidationError({'detail': 'Process already started.'})
            instance = ProcessInstance.objects.create(process=process, started_by=request.user)
            access_token = None
        else:
            token = secrets.token_urlsafe(48)
            expires = timezone.now() + timedelta(hours=24)
            instance = ProcessInstance.objects.create(
                process=process,
                started_by=None,
                access_token=token,
                access_token_expires_at=expires,
            )
            access_token = token

        instance.start()

        data = self.get_serializer(instance).data
        if access_token:
            return Response({'instance': data, 'access_token': access_token}, status=status.HTTP_201_CREATED)
        return Response(data, status=status.HTTP_201_CREATED)

class CurrentStepsFreeView(ListAPIView):
    serializer_class = FreeStepSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        instance_id = self.kwargs.get('pk')
        instance = ProcessInstance.objects.select_related('process').filter(pk=instance_id).first()
        if not instance:
            raise ValidationError({'detail': 'Instance not found.'})

        require_guest_token_if_needed(self.request, instance)

        submitted_ids = StepSubmission.objects.filter(instance=instance).values_list('step_id', flat=True)
        self._instance = instance
        self._submitted_ids = set(submitted_ids)
        return ProcessStep.objects.filter(process=instance.process).exclude(id__in=self._submitted_ids).order_by('order')

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        ser = self.get_serializer(qs, many=True, context={
            'instance': self._instance,
            'submitted_step_ids': self._submitted_ids
        })
        return Response(ser.data)

class SubmitFreeView(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = StepSubmissionSerializer

    def create(self, request, *args, **kwargs):
        instance = ProcessInstance.objects.select_related('process').filter(pk=self.kwargs.get('pk')).first()
        if not instance:
            raise ValidationError({'detail': 'Instance not found.'})

        require_guest_token_if_needed(request, instance)

        step_id = request.data.get('step')
        if not step_id:
            raise ValidationError({'detail': 'step is required.'})
        step = ProcessStep.objects.select_related('process', 'form').filter(pk=step_id).first()
        if not step:
            raise ValidationError({'detail': 'Step not found.'})
        if step.process_id != instance.process_id:
            raise ValidationError({'detail': 'Step does not belong to the instance process.'})

        if StepSubmission.objects.filter(instance=instance, step=step).exists():
            raise ValidationError({'detail': 'This step already submitted for this instance.'})

        ensure_form_password_if_private(step.form, request)

        fr = build_form_response_from_answers_or_skip(step.form, request)

        payload = {'instance': instance.id, 'step': step.id, 'form_response': fr.id}
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        instance.refresh_from_db()
        instance.mark_completed_if_done()

        return Response(ProcessInstanceSerializer(instance).data, status=status.HTTP_201_CREATED)

class SkipStepView(CreateAPIView):
    serializer_class = ProcessInstanceSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        instance = (ProcessInstance.objects.filter(pk=self.kwargs.get('pk')).select_related('current_step__form', 'process').first())
        if not instance:
            raise ValidationError({'detail': 'Instance not found.'})

        require_guest_token_if_needed(request, instance)

        if instance.process.type != Process.SEQUENTIAL:
            raise ValidationError({'detail': 'Skip is only allowed in sequential processes.'})

        step = instance.current_step
        if not step:
            raise ValidationError({'detail': 'Process already completed.'})

        if not step.allow_skip:
            raise ValidationError({'detail': 'This step cannot be skipped.'})

        if StepSubmission.objects.filter(instance=instance, step=step).exists():
            raise ValidationError({'detail': 'This step is already submitted.'})

        StepSubmission.objects.create(instance=instance, step=step, form_response=None, skipped=True)

        instance.advance_after_submission(step)
        instance.refresh_from_db()

        return Response(ProcessInstanceSerializer(instance).data, status=status.HTTP_201_CREATED)
