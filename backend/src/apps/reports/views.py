from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from apps.forms.models import Form
from apps.reports.serializers import (
    FormReportSerializer, 
    FormStatsSerializer,
    FormResponsesReportSerializer,
    )


class FormReportView(generics.RetrieveAPIView):
    queryset = Form.objects.all()
    serializer_class = FormReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'form_id'

    def get_object(self):
        form = super().get_object()
        if form.created_by != self.request.user:
            raise PermissionDenied("You don't have access to create report for this form.")
        return form


class FormStatsView(generics.RetrieveAPIView):
    queryset = Form.objects.all()
    serializer_class = FormStatsSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'form_id'

    def get_object(self):
        form = super().get_object()
        if form.created_by != self.request.user:
            raise PermissionDenied("You don't have access to create report for this form.")
        return form


class FormResponsesReportView(generics.RetrieveAPIView):
    queryset = Form.objects.all()
    serializer_class = FormResponsesReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'form_id'

    def get_object(self):
        form = super().get_object()
        if form.created_by != self.request.user:
            raise PermissionDenied("You don't have access to view responses for this form.")
        return form
