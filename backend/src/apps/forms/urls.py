from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.field_views import FieldViewSet

router = DefaultRouter()
router.register(r'fields', FieldViewSet, basename='fields')

urlpatterns = [
    path('', include(router.urls)),
]