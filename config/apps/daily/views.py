from datetime import timedelta

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.questions.models import Question

from .models import DailyChallenge, DailyChallengeAttempt
from .serializers import (
    DailyChallengeAttemptSerializer,
    DailyChallengeSerializer,
    DailySubmitSerializer,
)


QUESTIONS_PER_DAILY = 10
XP_PER_CORRECT = 10


class TodayDailyChallengeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        challenge = get_or_create_today_challenge()
        serializer = DailyChallengeSerializer(
            challenge,
            context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubmitDailyAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        challenge = get_or_create_today_challenge()
        if DailyChallengeAttempt.objects.filter(
            user=request.user,
            challenge=challenge,
        ).exists():
            raise ValidationError({'detail': 'Daily challenge already completed.'})

        serializer = DailySubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        challenge_questions = {
            question.id: question
            for question in challenge.questions.all()
        }
        score = 0
        for answer in serializer.validated_data['answers']:
            question = challenge_questions.get(answer['question_id'])
            if question is None:
                raise ValidationError(
                    {'answers': 'All answers must belong to today\'s challenge.'}
                )
            if answer['selected_index'] == question.correct_index:
                score += 1
                Question.objects.filter(id=question.id).update(
                    times_correct=F('times_correct') + 1
                )
            else:
                Question.objects.filter(id=question.id).update(
                    times_incorrect=F('times_incorrect') + 1
                )

        xp_earned = score * XP_PER_CORRECT
        attempt = DailyChallengeAttempt.objects.create(
            user=request.user,
            challenge=challenge,
            score=score,
            xp_earned=xp_earned,
        )
        update_user_daily_progress(request.user, xp_earned)

        return Response(
            DailyChallengeAttemptSerializer(attempt).data,
            status=status.HTTP_201_CREATED,
        )


class DailyHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        attempts = DailyChallengeAttempt.objects.select_related('challenge').filter(
            user=request.user,
        ).order_by('-completed_at')[:30]
        serializer = DailyChallengeAttemptSerializer(attempts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


def get_or_create_today_challenge():
    today = timezone.localdate()
    challenge, created = DailyChallenge.objects.get_or_create(
        date=today,
        defaults={'theme': 'Daily Bible Challenge'},
    )
    if created or challenge.questions.count() == 0:
        questions = list(
            Question.objects.filter(status='approved')
            .order_by('times_served', '?')[:QUESTIONS_PER_DAILY]
        )
        if len(questions) < QUESTIONS_PER_DAILY:
            raise ValidationError(
                {'detail': 'Not enough approved questions for today\'s challenge.'}
            )
        challenge.questions.set(questions)
        Question.objects.filter(id__in=[question.id for question in questions]).update(
            times_served=F('times_served') + 1
        )
    return challenge


def update_user_daily_progress(user, xp_earned):
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)

    if user.last_played_date == today:
        new_streak = user.current_streak
    elif user.last_played_date == yesterday:
        new_streak = user.current_streak + 1
    else:
        new_streak = 1

    user.total_xp = F('total_xp') + xp_earned
    user.current_streak = new_streak
    user.longest_streak = max(user.longest_streak, new_streak)
    user.last_played_date = today
    user.save(
        update_fields=[
            'total_xp',
            'current_streak',
            'longest_streak',
            'last_played_date',
        ]
    )
