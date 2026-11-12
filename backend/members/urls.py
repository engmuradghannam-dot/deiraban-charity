from django.urls import path
from .views import MyMemberDocumentView, MyMemberPersonalDataView, MyMemberProfilePhotoView, MyMemberView, RegisterMemberView

urlpatterns = [
    path('me/personal/', MyMemberPersonalDataView.as_view(), name='my-member-personal'),
    path('me/profile-photo/', MyMemberProfilePhotoView.as_view(), name='my-member-profile-photo'),
    path('me/document/<str:document_type>/', MyMemberDocumentView.as_view(), name='my-member-document'),
    path('me/', MyMemberView.as_view(), name='my-member'),
    path('register/', RegisterMemberView.as_view(), name='register-member'),
]
