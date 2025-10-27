from django.urls import path
from .views import StartProcessView, CurrentStepView, SubmitStepView, ProcessListCreateView, ProcessRUDView, \
    StepListCreateView, StepRUDView
# from .views import (
#     FreeFlowProcessListCreateView,
#     FreeFlowStartProcessView,
#     FreeFlowSubmitStepView,
# )


urlpatterns = [
    path('', ProcessListCreateView.as_view(), name='process-list-create'),
    path('<int:pk>/', ProcessRUDView.as_view(), name='process-detail'),

    path('<int:process_id>/steps/', StepListCreateView.as_view(), name='step-list-create'),
    path('steps/<int:pk>/', StepRUDView.as_view(), name='step-detail'),

    path('<int:pk>/start/', StartProcessView.as_view(), name='process-start'),
    path('instances/<int:pk>/current-step/', CurrentStepView.as_view(), name='current-step'),
    path('instances/<int:pk>/submit-step/', SubmitStepView.as_view(), name='submit-step'),
    
    # #freeflow
    # path('freeflow/', FreeFlowProcessListCreateView.as_view(), name='freeflow-process-list-create'),
    # path('freeflow/<int:pk>/start/', FreeFlowStartProcessView.as_view(), name='freeflow-process-start'),
    # path('freeflow/instances/<int:pk>/submit-step/', FreeFlowSubmitStepView.as_view(), name='freeflow-submit-step'),

]