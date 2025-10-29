from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.categories.models import FormCategory,ProcessCategory
from apps.categories.serializer import FormCategorySerializer,ProcessCategorySerializer
from apps.forms.models import Form
from apps.processes.models import Process


class FormCategoryViewSet(viewsets.ModelViewSet):
    queryset = FormCategory.objects.all()
    serializer_class = FormCategorySerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        queryset = FormCategory.objects.all()
        forms_id = self.request.query_params.get('form')
        if forms_id is not None:
            queryset = queryset.filter(forms__id=forms_id)
        return queryset

    @action(detail=True, methods=['post'], url_path='add-form')
    def add_form(self, request, pk=None):
        category = self.get_object()
        form_id = request.data.get('form_id')
        if not form_id:
            return Response({'error': 'form_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            form = Form.objects.get(id=form_id)
        except Form.DoesNotExist:
            return Response({'error': 'Form not found'}, status=status.HTTP_404_NOT_FOUND)
        if category.forms.filter(id=form_id).exists():
            return Response({'error': 'form already added'}, status=status.HTTP_400_BAD_REQUEST)

        category.forms.add(form)
        return Response({'message': f'Form {form.id} added to category {category.id}'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='remove-form')
    def remove_form(self, request, pk=None):
        category = self.get_object()
        form_id = request.data.get('form_id')
        if not form_id:
            return Response({'error': 'form_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            form = Form.objects.get(id=form_id)
        except Form.DoesNotExist:
            return Response({'error': 'Form not found'}, status=status.HTTP_404_NOT_FOUND)

        category.forms.remove(form)
        return Response({'message': f'Form {form.id} removed from category {category.id}'}, status=status.HTTP_200_OK)

class ProcessCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProcessCategory.objects.all()
    serializer_class = ProcessCategorySerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        queryset = ProcessCategory.objects.all()
        process_id = self.request.query_params.get('process')
        if process_id is not None:
            queryset = queryset.filter(process__id=process_id)
        return queryset

    @action(detail=True, methods=['post'], url_path='add-process')
    def add_process(self, request, pk=None):
        category = self.get_object()
        process_id = request.data.get('process_id')
        if not process_id:
            return Response({'error': 'process_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            process = Process.objects.get(id=process_id)
        except Process.DoesNotExist:
            return Response({'error': 'Process not found'}, status=status.HTTP_404_NOT_FOUND)
        if category.process.filter(id=process_id).exists():
            return Response({'error': 'Process already added'}, status=status.HTTP_400_BAD_REQUEST)

        category.process.add(process)
        return Response({'message': f'Process {process.id} added to category {category.id}'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='remove-process')
    def remove_process(self, request, pk=None):
        category = self.get_object()
        process_id = request.data.get('process_id')
        if not process_id:
            return Response({'error': 'process_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            process = Process.objects.get(id=process_id)
        except Process.DoesNotExist:
            return Response({'error': 'Process not found'}, status=status.HTTP_404_NOT_FOUND)

        category.process.remove(process)
        return Response({'message': f'Process {process.id} removed from category {category.id}'}, status=status.HTTP_200_OK)
