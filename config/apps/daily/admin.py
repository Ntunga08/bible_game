from django.contrib import admin

from .models import (
    DailyChallenge,
    DailyChallengeAnswer,
    DailyChallengeAttempt,
    DailyChallengeQuestion,
)


class DailyChallengeQuestionInline(admin.TabularInline):
    model = DailyChallengeQuestion
    extra = 0
    fields = ['order', 'question']


@admin.register(DailyChallenge)
class DailyChallengeAdmin(admin.ModelAdmin):
    list_display = ['date', 'title', 'is_active', 'created_at']
    list_filter = ['is_active', 'date']
    search_fields = ['title']
    inlines = [DailyChallengeQuestionInline]


@admin.register(DailyChallengeQuestion)
class DailyChallengeQuestionAdmin(admin.ModelAdmin):
    list_display = ['challenge', 'order', 'question']
    list_filter = ['challenge__date', 'question__difficulty']
    search_fields = ['question__question_text']


@admin.register(DailyChallengeAttempt)
class DailyChallengeAttemptAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'challenge',
        'score',
        'correct_answers',
        'wrong_answers',
        'time_taken_seconds',
        'completed_at',
    ]
    list_filter = ['challenge__date', 'completed_at']
    search_fields = ['user__username', 'challenge__title']


@admin.register(DailyChallengeAnswer)
class DailyChallengeAnswerAdmin(admin.ModelAdmin):
    list_display = [
        'attempt',
        'question',
        'selected_index',
        'is_correct',
        'time_taken_seconds',
        'answered_at',
    ]
    list_filter = ['is_correct', 'answered_at']
    search_fields = ['attempt__user__username', 'question__question_text']
