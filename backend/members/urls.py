from django.urls import path
from .views import MyMemberPersonalDataView, MyMemberProfilePhotoView, MyMemberView, RegisterMemberView

urlpatterns = [
    path('me/personal/', MyMemberPersonalDataView.as_view(), name='my-member-personal'),
    path('me/profile-photo/', MyMemberProfilePhotoView.as_view(), name='my-member-profile-photo'),
    path('me/', MyMemberView.as_view(), name='my-member'),
    path('register/', RegisterMemberView.as_view(), name='register-member'),
]
