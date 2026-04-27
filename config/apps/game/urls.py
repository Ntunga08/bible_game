from django.urls import path

from .views import (
    CompleteLevelView,
    GameQuestionsView,
    GameStatusView,
    RetryLevelView,
    StartGameView,
    SubmitAnswerView,
)


urlpatterns = [
    path('start/', StartGameView.as_view(), name='game-start'),
    path('answer/', SubmitAnswerView.as_view(), name='game-answer'),
    path('<uuid:session_id>/', GameStatusView.as_view(), name='game-status'),
    path(
        '<uuid:session_id>/questions/',
        GameQuestionsView.as_view(),
        name='game-questions',
    ),
    path(
        '<uuid:session_id>/complete-level/',
        CompleteLevelView.as_view(),
        name='game-complete-level',
    ),
    path('<uuid:session_id>/retry/', RetryLevelView.as_view(), name='game-retry'),
]
