from django.urls import path
from .views import MyMemberView, RegisterMemberView

urlpatterns = [
    path('me/', MyMemberView.as_view(), name='my-member'),
    path('register/', RegisterMemberView.as_view(), name='register-member'),
]
