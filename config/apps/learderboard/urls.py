from django.urls import path

from .views import LeaderboardView, MyLeaderboardRankView


urlpatterns = [
    path('', LeaderboardView.as_view(), name='leaderboard-list'),
    path('me/', MyLeaderboardRankView.as_view(), name='leaderboard-me'),
]
