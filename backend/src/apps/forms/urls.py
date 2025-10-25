from rest_framework.routers import DefaultRouter
from .views import FieldViewSet, FormViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r'forms', FormViewSet)
router.register(r'fields', FieldViewSet)
router.register(r'categories', CategoryViewSet)

urlpatterns = router.urls
