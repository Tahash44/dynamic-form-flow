from rest_framework.routers import DefaultRouter
from .views import FieldViewSet, FormViewSet, ResponseViewSet

router = DefaultRouter()
router.register(r'forms', FormViewSet)
router.register(r'fields', FieldViewSet)
router.register(r'response', ResponseViewSet)

urlpatterns = router.urls
