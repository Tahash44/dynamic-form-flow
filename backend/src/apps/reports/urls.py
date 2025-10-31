from django.urls import path
from reports.views import FormReportView, FormStatsView

urlpatterns = [
    path('<int:form_id/report/', FormReportView.as_view(), name='form-report'),
    path('<int:form_id/stats/', FormStatsView.as_view(), name='form-stats'),
]