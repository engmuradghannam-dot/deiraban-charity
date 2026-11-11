from django.urls import path
from .views import MyMemberPersonalDataView, MyMemberView, RegisterMemberView

urlpatterns = [
    path('me/personal/', MyMemberPersonalDataView.as_view(), name='my-member-personal'),
    path('me/', MyMemberView.as_view(), name='my-member'),
    path('register/', RegisterMemberView.as_view(), name='register-member'),
]
