from rest_framework.routers import DefaultRouter
from apps.categories.views import FormCategoryViewSet,ProcessCategoryViewSet


router = DefaultRouter()

router.register(r'form-categories', FormCategoryViewSet)
router.register(r'process-categories', ProcessCategoryViewSet)
urlpatterns = router.urls
