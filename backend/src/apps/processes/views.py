from rest_framework import status, filters
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, ListCreateAPIView, \
    RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from .models import Process, ProcessInstance, ProcessStep, StepSubmission
from .permissions import IsOwnerOrReadOnly
from .serializers import ProcessSerializer, ProcessStepSerializer, ProcessInstanceSerializer, StepSubmissionSerializer, \
    ProcessWriteSerializer, ProcessStepWriteSerializer


class ProcessListView(ListAPIView):
    queryset = Process.objects.filter(is_active=True, type=Process.SEQUENTIAL)
    serializer_class = ProcessSerializer
    permission_classes = [IsAuthenticated]


class StartProcessView(CreateAPIView):
    serializer_class = ProcessInstanceSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        try:
            process = Process.objects.get(pk=pk, is_active=True, type=Process.SEQUENTIAL)
        except Process.DoesNotExist:
            raise ValidationError({'detail': 'Process not found or inactive.'})

        existing = ProcessInstance.objects.filter(
            process=process, started_by=request.user, status='running'
        ).first()
        if existing:
            raise ValidationError({'detail': 'Process already started.'})

        instance = ProcessInstance.objects.create(process=process, started_by=request.user)
        instance.start()

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CurrentStepView(RetrieveAPIView):
    queryset = ProcessInstance.objects.all()
    serializer_class = ProcessStepSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        instance = super().get_object()
        if instance.started_by != self.request.user:
            raise ValidationError({'detail': 'Access denied.'})
        return instance

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.current_step:
            return Response({'detail': 'Process completed.'})
        data = self.get_serializer(instance.current_step).data
        return Response(data)


class SubmitStepView(CreateAPIView):
    serializer_class = StepSubmissionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        instance_id = self.kwargs.get('pk')

        try:
            instance = ProcessInstance.objects.get(pk=instance_id, started_by=request.user)
        except ProcessInstance.DoesNotExist:
            raise ValidationError({'detail': 'Instance not found.'})

        step = instance.current_step
        if not step:
            raise ValidationError({'detail': 'Process already completed.'})

        form_response_id = request.data.get('form_response')
        if not form_response_id:
            raise ValidationError({'detail': 'form_response ID is required.'})

        serializer = self.get_serializer(data={
            'instance': instance.id,
            'step': step.id,
            'form_response': form_response_id,
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
        return super().get_queryset()


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
        self.check_object_permissions(self.request, process)  # IsOwnerOrReadOnly روی process
        serializer.save(process=process)


class StepRUDView(RetrieveUpdateDestroyAPIView):
    queryset = ProcessStep.objects.select_related('process')
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_serializer_class(self):
        return ProcessStepWriteSerializer if self.request.method in ('PUT', 'PATCH') else ProcessStepSerializer
