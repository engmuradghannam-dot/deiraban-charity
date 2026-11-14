from django.contrib import admin
from django.urls import include, path

from members.views import GoogleLogin, LinkGoogleAccount, MemberPasswordLogin, MemberSearch

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/google/", GoogleLogin.as_view(), name="google_login"),
    path("api/auth/google/link/", LinkGoogleAccount.as_view(), name="google_link"),
    path("api/auth/member-login/", MemberPasswordLogin.as_view(), name="member_password_login"),
    path("api/auth/member-search/", MemberSearch.as_view(), name="member_search"),
    path("api/members/", include("members.urls")),
    path("api/elections/", include("elections.urls")),
    path("api/donations/", include("donations.urls")),
    path("api/registry/", include("membership.urls")),
    path("api/aid-requests/", include("aid_requests.urls")),
]
