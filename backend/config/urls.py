from django.contrib import admin
from django.urls import include, path

from members.views import GoogleLogin

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/google/", GoogleLogin.as_view(), name="google_login"),
    path("api/members/", include("members.urls")),
    path("api/elections/", include("elections.urls")),
    path("api/donations/", include("donations.urls")),
    path("api/registry/", include("membership.urls")),
]
