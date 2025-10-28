from django.urls import path
from .views import StartProcessView, CurrentStepView, SubmitStepView, ProcessListCreateView, ProcessRUDView, \
    StepListCreateView, StepRUDView, ProcessFreeListView, StartFreeProcessView, CurrentStepsFreeView, \
    SubmitFreeStepView, ProcessSequentialListView, ProcessListView

# from .views import (
#     FreeFlowProcessListCreateView,
#     FreeFlowStartProcessView,
#     FreeFlowSubmitStepView,
# )


urlpatterns = [
    path('', ProcessListView.as_view(), name='process-list'),
    path('free/', ProcessFreeListView.as_view(), name='free-process-list'),
    path('sequ/', ProcessSequentialListView.as_view(), name='free-process-list'),


    path('list/', ProcessListCreateView.as_view(), name='process-list-create'),
    path('<int:pk>/', ProcessRUDView.as_view(), name='process-detail'),

    path('<int:process_id>/steps/', StepListCreateView.as_view(), name='step-list-create'),
    path('steps/<int:pk>/', StepRUDView.as_view(), name='step-detail'),

    path('<int:pk>/start/', StartProcessView.as_view(), name='process-start'),
    path('instances/<int:pk>/current-step/', CurrentStepView.as_view(), name='current-step'),
    path('instances/<int:pk>/submit-step/', SubmitStepView.as_view(), name='submit-step'),


    path('free/<int:pk>/start/', StartFreeProcessView.as_view(), name='free-process-start'),
    path('instances/<int:pk>/current-steps/', CurrentStepsFreeView.as_view(), name='free-current-steps'),
    path('instances/<int:pk>/submit-free-step/', SubmitFreeStepView.as_view(), name='free-submit-free-step'),

]