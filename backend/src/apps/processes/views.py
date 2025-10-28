import secrets
from datetime import timedelta, datetime
from rest_framework_simplejwt.tokens import AccessToken
from django.utils import timezone
from rest_framework import status, filters
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, ListCreateAPIView, \
    RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
import pytz
from .models import Process, ProcessInstance, ProcessStep, StepSubmission
from .permissions import IsOwnerOrReadOnly
from .serializers import ProcessSerializer, ProcessStepSerializer, ProcessInstanceSerializer, StepSubmissionSerializer, \
    ProcessWriteSerializer, ProcessStepWriteSerializer, FreeStepSerializer


# from .serializers import (
#     FreeFlowProcessSerializer,
#     FreeFlowProcessWriteSerializer,
#     #FreeFlowStepWriteSerializer,
# )

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

    token = get_instance_token_from_request(request)
    if not token:
        raise ValidationError({'detail': 'Guest instance token is required.'})

    if token != (instance.access_token or ''):
        raise ValidationError({'detail': 'Invalid guest token.'})

    if instance.access_token_expires_at and timezone.now() > instance.access_token_expires_at:
        raise ValidationError({'detail': 'Guest token expired.'})


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
            token = secrets.token_urlsafe(48)
            expires = timezone.now() + timedelta(hours=24)
            instance = ProcessInstance(
                process=process,
                started_by=None,
                access_token=token,
                access_token_expires_at=expires,
            )
            instance.save()
            access_token = token
        else:
            token_obj = request.auth
            token_str = str(token_obj)
            expires_at = None
            if token_obj:
                try:
                    at = AccessToken(token_str)
                    expires_timestamp = at['exp']
                    expires_at = datetime.fromtimestamp(expires_timestamp, tz=pytz.UTC)
                except Exception:
                    expires_at = None
            instance = ProcessInstance.objects.create(
                process=process,
                started_by=request.user,
                access_token=token_str,
                access_token_expires_at=expires_at,
            )
            access_token = None

        instance.start()

        data = self.get_serializer(instance).data
        if access_token:
            return Response({'instance': data, 'access_token': access_token}, status=status.HTTP_201_CREATED)
        return Response(data, status=status.HTTP_201_CREATED)


class CurrentStepView(RetrieveAPIView):
    queryset = ProcessInstance.objects.select_related('current_step__form', 'process')
    serializer_class = ProcessStepSerializer
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        require_guest_token_if_needed(request, instance)

        step = instance.current_step
        if not step:
            return Response({'detail': 'Process completed.'})

        step = instance.current_step
        if not step:
            return Response({'detail': 'Process completed.'})

        ensure_form_password_if_private(step.form, request)
        return Response(self.get_serializer(step).data)


class SubmitStepView(CreateAPIView):
    serializer_class = StepSubmissionSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        instance = (ProcessInstance.objects.filter(pk=self.kwargs.get('pk')).select_related('current_step__form', 'process').first())
        if not instance:
            raise ValidationError({'detail': 'Instance not found.'})

        require_guest_token_if_needed(request, instance)

        step = instance.current_step
        if not step:
            raise ValidationError({'detail': 'Process already completed.'})

        form = step.form
        ensure_form_password_if_private(form, request)

        form_response_id = request.data.get('form_response')
        if not form_response_id:
            raise ValidationError({'detail': 'form_response ID is required.'})

        from apps.forms.models import Response as FormResponse
        fr = (FormResponse.objects.select_related('form', 'user').filter(pk=form_response_id).first())
        if not fr:
            raise ValidationError({'detail': 'form_response not found.'})
        if fr.form_id != form.id:
            raise ValidationError({'detail': 'form_response does not belong to the current step form.'})
        if request.user.is_authenticated and fr.user_id != request.user.id:
            raise ValidationError({'detail': 'form_response belongs to a different user.'})

        serializer = self.get_serializer(data={
            'instance': instance.id,
            'step': step.id,
            'form_response': fr.id,
        })
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()

        instance.advance_after_submission(step)

        instance.refresh_from_db()
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

class SubmitFreeStepView(CreateAPIView):
    serializer_class = StepSubmissionSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        instance_id = self.kwargs.get('pk')
        instance = ProcessInstance.objects.select_related('process').filter(pk=instance_id).first()
        if not instance:
            raise ValidationError({'detail': 'Instance not found.'})

        require_guest_token_if_needed(request, instance)

        step_id = request.data.get('step')
        form_response_id = request.data.get('form_response')
        if not step_id or not form_response_id:
            raise ValidationError({'detail': 'step and form_response are required.'})

        step = ProcessStep.objects.select_related('form', 'process').filter(pk=step_id).first()
        if not step:
            raise ValidationError({'detail': 'Step not found.'})
        if step.process_id != instance.process_id:
            raise ValidationError({'detail': 'Step does not belong to this process instance.'})

        if StepSubmission.objects.filter(instance=instance, step=step).exists():
            raise ValidationError({'detail': 'This step is already submitted for this instance.'})

        ensure_form_password_if_private(step.form, request)

        from apps.forms.models import Response as FormResponse
        fr = FormResponse.objects.select_related('form', 'user').filter(pk=form_response_id).first()
        if not fr:
            raise ValidationError({'detail': 'form_response not found.'})
        if fr.form_id != step.form_id:
            raise ValidationError({'detail': 'form_response does not belong to the step form.'})
        if request.user.is_authenticated and fr.user_id and fr.user_id != request.user.id:
            raise ValidationError({'detail': 'form_response belongs to a different user.'})

        StepSubmission.objects.create(instance=instance, step=step, form_response=fr)

        instance.mark_completed_if_done()

        return Response(ProcessInstanceSerializer(instance).data, status=status.HTTP_201_CREATED)
