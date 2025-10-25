from django.utils import timezone
from django.core.cache import cache
from rest_framework import status, filters
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, ListCreateAPIView, \
    RetrieveUpdateDestroyAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError

from .models import Process, ProcessInstance, ProcessStep
from .permissions import IsOwnerOrReadOnly
from .serializers import ProcessSerializer, ProcessStepSerializer, ProcessInstanceSerializer, StepSubmissionSerializer, \
    ProcessWriteSerializer, ProcessStepWriteSerializer

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


@method_decorator(cache_page(60 * 5), name='dispatch')
class ProcessListView(ListAPIView):
    queryset = Process.objects.filter(is_active=True, type=Process.SEQUENTIAL)
    serializer_class = ProcessSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['created_at', 'title']


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


class StartProcessView(CreateAPIView):
    serializer_class = ProcessInstanceSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        try:
            process = Process.objects.get(pk=pk, is_active=True, type=Process.SEQUENTIAL)
        except Process.DoesNotExist:
            raise ValidationError({'detail': 'Process not found or inactive.'})

        if request.user.is_authenticated:
            existing = ProcessInstance.objects.filter(
                process=process, started_by=request.user, status='running'
            ).first()
            if existing:
                raise ValidationError({'detail': 'Process already started.'})

        instance = ProcessInstance.objects.create(
            process=process,
            started_by=request.user if request.user.is_authenticated else None
        )
        instance.start()

        access_token = None
        if not request.user.is_authenticated:
            instance.issue_guest_token()
            access_token = instance.access_token

        data = self.get_serializer(instance).data
        if access_token:
            return Response({'instance': data, 'access_token': access_token}, status=status.HTTP_201_CREATED)
        return Response(data, status=status.HTTP_201_CREATED)

class CurrentStepView(RetrieveAPIView):
    queryset = ProcessInstance.objects.select_related('current_step__form', 'process').only('current_step__form__password', 'current_step__form__access')
    serializer_class = ProcessStepSerializer
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        require_guest_token_if_needed(request, instance)

        cache_key = f'current_step_{instance.id}'
        data = cache.get(cache_key)
        if data:
            return Response(data)

        step = instance.current_step
        if not step:
            return Response({'detail': 'Process completed.'})

        form = step.form
        if getattr(form, 'access', 'public') == 'private':
            provided = request.query_params.get('password') or request.headers.get('X-Form-Password')
            if provided != (getattr(form, 'password', '') or ''):
                raise ValidationError({'detail': 'Form is private. Password required or incorrect.'})

        data = self.get_serializer(step).data
        cache.set(cache_key, data, 10)
        return Response(data)


class SubmitStepView(CreateAPIView):
    serializer_class = StepSubmissionSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        instance = ProcessInstance.objects.filter(pk=self.kwargs.get('pk')).select_related('current_step__form', 'process').first()
        if not instance:
            raise ValidationError({'detail': 'Instance not found.'})

        require_guest_token_if_needed(request, instance)

        step = instance.current_step
        if not step:
            raise ValidationError({'detail': 'Process already completed.'})

        form = step.form
        if getattr(form, 'access', 'public') == 'private':
            provided = request.data.get('password') or request.headers.get('X-Form-Password')
            if provided != (getattr(form, 'password', '') or ''):
                raise ValidationError({'detail': 'Incorrect form password.'})

        form_response_id = request.data.get('form_response')
        if not form_response_id:
            raise ValidationError({'detail': 'form_response ID is required.'})

        from apps.forms.models import Response as FormResponse
        fr = FormResponse.objects.select_related('form', 'user').filter(pk=form_response_id).first()
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
        serializer.save()

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


@method_decorator(cache_page(60 * 10), name='get')
class ProcessRUDView(RetrieveUpdateDestroyAPIView):
    queryset = Process.objects.filter(type=Process.SEQUENTIAL)
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_serializer_class(self):
        return ProcessWriteSerializer if self.request.method in ('PUT', 'PATCH') else ProcessSerializer

    def perform_destroy(self, instance):
        if instance.instances.exists():
            raise ValidationError({'detail': 'Process cannot be deleted because instances exist.'})
        instance.delete()


class StepListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return ProcessStep.objects.filter(process_id=self.kwargs['process_id']).select_related('process')

    def get_serializer_class(self):
        return ProcessStepWriteSerializer if self.request.method == 'POST' else ProcessStepSerializer

    def perform_create(self, serializer):
        process = Process.objects.get(pk=self.kwargs['process_id'], type=Process.SEQUENTIAL)
        self.check_object_permissions(self.request, process)  # IsOwnerOrReadOnly روی process
        serializer.save(process=process)


class StepRUDView(RetrieveUpdateDestroyAPIView):
    queryset = ProcessStep.objects.select_related('process')
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_serializer_class(self):
        return ProcessStepWriteSerializer if self.request.method in ('PUT', 'PATCH') else ProcessStepSerializer

    def perform_destroy(self, instance):
        if instance.process.instances.exists():
            raise ValidationError({'detail': 'Cannot delete step because process has running or completed instances.'})
        instance.delete()

    def perform_update(self, serializer):
        process = serializer.instance.process
        if process.instances.exists():
            raise ValidationError({'detail': 'Cannot edit step because process already has instances.'})
        serializer.save()


class CloseProcessView(UpdateAPIView):
    queryset = Process.objects.all()
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    serializer_class = ProcessSerializer

    def update(self, request, *args, **kwargs):
        process = self.get_object()
        process.is_active = False
        process.save(update_fields=['is_active'])
        cache.delete_pattern('views.decorators.cache.cache_page.*')
        return Response({
            'detail': 'Process closed successfully.',
            'process': ProcessSerializer(process).data
        })
