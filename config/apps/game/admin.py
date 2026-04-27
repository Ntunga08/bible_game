from django.contrib import admin

from .models import GameSession, SessionQuestion, UserQuestionHistory


class SessionQuestionInline(admin.TabularInline):
    model = SessionQuestion
    extra = 0
    readonly_fields = ['id', 'question', 'selected_index', 'is_correct', 'answered_at']


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'current_level',
        'score',
        'correct_answers',
        'status',
        'started_at',
        'ended_at',
    ]
    list_filter = ['current_level', 'status', 'started_at']
    search_fields = ['id', 'user__username']
    inlines = [SessionQuestionInline]


@admin.register(SessionQuestion)
class SessionQuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'question', 'selected_index', 'is_correct']
    list_filter = ['is_correct', 'question__difficulty']
    search_fields = ['session__id', 'question__question_text']


@admin.register(UserQuestionHistory)
class UserQuestionHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'question', 'times_seen', 'times_correct', 'last_seen_at']
    search_fields = ['user__username', 'question__question_text']
