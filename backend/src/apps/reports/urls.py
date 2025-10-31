from django.urls import path
from apps.reports.views import (
    FormReportView, 
    FormStatsView,
    FormResponsesReportView
    )

urlpatterns = [
    path('<int:form_id>/report/', FormReportView.as_view(), name='form-report'),
    path('<int:form_id>/stats/', FormStatsView.as_view(), name='form-stats'),
    path('<int:form_id>/responses/', FormResponsesReportView.as_view(), name='form-responses-report'),
]