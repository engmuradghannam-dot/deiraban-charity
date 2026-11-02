from django.urls import path
from .views import (ElectionListView, ElectionDetailView, VoteView,
                    ElectionResultsView)

urlpatterns = [
    path('', ElectionListView.as_view(), name='election-list'),
    path('<int:pk>/', ElectionDetailView.as_view(), name='election-detail'),
    path('<int:pk>/vote/', VoteView.as_view(), name='election-vote'),
    path('<int:pk>/results/', ElectionResultsView.as_view(), name='election-results'),
]
