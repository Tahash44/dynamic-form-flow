
from django.urls import path
from reports.views import FormReportView

urlpatterns = [
    path('<int:form_id/report/', FormReportView.as_view(), name='form-report'),
]