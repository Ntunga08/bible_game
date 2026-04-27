from django.urls import path

from .views import (
    CompleteDailyChallengeView,
    DailyHistoryView,
    DailyLeaderboardView,
    StartDailyChallengeView,
    SubmitDailyAnswerView,
    TodayDailyChallengeView,
)


urlpatterns = [
    path('today/', TodayDailyChallengeView.as_view(), name='daily-today'),
    path('start/', StartDailyChallengeView.as_view(), name='daily-start'),
    path('answer/', SubmitDailyAnswerView.as_view(), name='daily-answer'),
    path('complete/', CompleteDailyChallengeView.as_view(), name='daily-complete'),
    path('leaderboard/', DailyLeaderboardView.as_view(), name='daily-leaderboard'),
    path('history/', DailyHistoryView.as_view(), name='daily-history'),
]
