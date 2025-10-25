from rest_framework.routers import DefaultRouter
from .views import FieldViewSet, FormViewSet

router = DefaultRouter()
router.register(r'forms', FormViewSet)
router.register(r'fields', FieldViewSet)

urlpatterns = router.urls
