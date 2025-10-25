from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.categories.models import FormCategory
from apps.categories.serializer import CategorySerializer
from apps.forms.models import Form

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = FormCategory.objects.all()
    serializer_class = CategorySerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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
