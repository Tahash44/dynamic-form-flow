from django.utils import timezone
from rest_framework import viewsets

from rest_framework.response import Response

from .models import Form, Field, Response
from .serializer import FormSerializer, FieldSerializer, ResponseSerializer


class FieldViewSet(viewsets.ModelViewSet):
    queryset = Field.objects.all()
    serializer_class = FieldSerializer


class FormViewSet(viewsets.ModelViewSet):
    queryset = Form.objects.all()
    serializer_class = FormSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views_count = (instance.views_count or 0) + 1
        instance.save(update_fields=['views_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data) 


class ResponseViewSet(viewsets.ModelViewSet):
    queryset = Response.objects.all()
    serializer_class = ResponseSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        queryset = Response.objects.all()
        form_id = self.request.query_params.get('form')
        if form_id is not None:
            queryset = queryset.filter(form_id=form_id)
        return queryset
