from django.db.models import F
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from apps.game.models import UserQuestionHistory

from .models import Category, Question
from .serializers import (
    CategorySerializer,
    CheckAnswerSerializer,
    PlayerQuestionSerializer,
    QuestionSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.select_related('category').all().order_by('-created_at')
    serializer_class = QuestionSerializer

    def get_permissions(self):
        player_actions = ['level', 'check_answer']
        if self.action in player_actions:
            return [AllowAny()]
        return [IsAdminUser()]

    def get_queryset(self):
        queryset = super().get_queryset()
        difficulty = self.request.query_params.get('difficulty')
        status_filter = self.request.query_params.get('status')
        category = self.request.query_params.get('category')

        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if category:
            queryset = queryset.filter(category_id=category)
        return queryset

    def perform_create(self, serializer):
        serializer.save(ai_generated=False)

    def perform_destroy(self, instance):
        instance.status = 'archived'
        instance.save(update_fields=['status', 'updated_at'])

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def archive(self, request, pk=None):
        question = self.get_object()
        question.status = 'archived'
        question.save(update_fields=['status', 'updated_at'])
        return Response(QuestionSerializer(question).data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get'],
        url_path=r'level/(?P<level>[1-5])',
        permission_classes=[AllowAny],
    )
    def level(self, request, level=None):
        level = int(level)
        count = self._get_count(request)
        queryset = Question.objects.select_related('category').filter(
            difficulty=level,
            status='approved',
        )

        if request.user.is_authenticated:
            recent_ids = UserQuestionHistory.objects.filter(
                user=request.user,
                question__difficulty=level,
            ).order_by('-last_seen_at').values_list('question_id', flat=True)[:50]
            fresh_queryset = queryset.exclude(id__in=list(recent_ids))
            if fresh_queryset.exists():
                queryset = fresh_queryset

        questions = list(queryset.order_by('times_served', '?')[:count])

        if not questions:
            return Response([], status=status.HTTP_200_OK)

        question_ids = [question.id for question in questions]
        Question.objects.filter(id__in=question_ids).update(
            times_served=F('times_served') + 1
        )

        for question in questions:
            question.times_served += 1

        if request.user.is_authenticated:
            for question in questions:
                history, created = UserQuestionHistory.objects.get_or_create(
                    user=request.user,
                    question=question,
                )
                if not created:
                    history.times_seen = F('times_seen') + 1
                    history.save(update_fields=['times_seen', 'last_seen_at'])

        serializer = PlayerQuestionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['post'],
        url_path='check-answer',
        permission_classes=[AllowAny],
    )
    def check_answer(self, request):
        serializer = CheckAnswerSerializer(data=request.data, context={})
        serializer.is_valid(raise_exception=True)

        question = serializer.context['question']
        selected_index = serializer.validated_data['selected_index']
        is_correct = selected_index == question.correct_index

        if is_correct:
            Question.objects.filter(id=question.id).update(
                times_correct=F('times_correct') + 1
            )
        else:
            Question.objects.filter(id=question.id).update(
                times_incorrect=F('times_incorrect') + 1
            )

        return Response(
            {
                'is_correct': is_correct,
                'correct_index': question.correct_index,
                'explanation': question.explanation,
                'bible_reference': question.bible_reference,
            },
            status=status.HTTP_200_OK,
        )

    def _get_count(self, request):
        raw_count = request.query_params.get('count', 10)
        try:
            count = int(raw_count)
        except (TypeError, ValueError):
            count = 10
        return max(1, min(count, 50))
