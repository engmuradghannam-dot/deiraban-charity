from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AidRequestAdminViewSet, register_aid_request

router = DefaultRouter()
router.register("admin", AidRequestAdminViewSet, basename="aid-request-admin")

urlpatterns = [
    path("register/", register_aid_request, name="aid-request-register"),
    path("", include(router.urls)),
]
