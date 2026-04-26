from django.contrib import admin

from .models import Category, Question


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'icon']
    search_fields = ['name', 'display_name']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = [
        'question_text',
        'difficulty',
        'testament',
        'category',
        'status',
        'quality_score',
        'ai_generated',
    ]
    list_filter = ['difficulty', 'testament', 'category', 'status', 'ai_generated']
    search_fields = ['question_text', 'bible_reference', 'book_name']
    readonly_fields = [
        'times_served',
        'times_correct',
        'times_incorrect',
        'correct_rate',
        'created_at',
        'updated_at',
    ]
