from django.urls import path
from .views import ProcessListView, StartProcessView, CurrentStepView, SubmitStepView

urlpatterns = [
    path('processes/', ProcessListView.as_view(), name='process-list'),
    path('processes/<int:pk>/start/', StartProcessView.as_view(), name='process-start'),
    path('instances/<int:pk>/current-step/', CurrentStepView.as_view(), name='current-step'),
    path('instances/<int:pk>/submit-step/', SubmitStepView.as_view(), name='submit-step'),
]
