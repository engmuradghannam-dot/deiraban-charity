from rest_framework.routers import DefaultRouter
from .views import FamilyViewSet, MemberViewSet

router = DefaultRouter()
router.register(r"families", FamilyViewSet, basename="family")
router.register(r"members", MemberViewSet, basename="member")

urlpatterns = router.urls
