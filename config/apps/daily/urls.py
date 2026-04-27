from django.urls import path

from .views import DailyHistoryView, TodayDailyChallengeView, SubmitDailyAnswerView


urlpatterns = [
    path('today/', TodayDailyChallengeView.as_view(), name='daily-today'),
    path('answer/', SubmitDailyAnswerView.as_view(), name='daily-answer'),
    path('history/', DailyHistoryView.as_view(), name='daily-history'),
]
