from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DailyChallengeAttempt
from .serializers import (
    DailyAnswerSerializer,
    DailyAttemptHistorySerializer,
    DailyChallengeTodaySerializer,
    DailyCompleteSerializer,
    DailyLeaderboardSerializer,
    DailyStartSerializer,
)
from .services import (
    answer_daily_question,
    complete_daily_attempt,
    ensure_daily_unlocked,
    get_or_create_today_challenge,
    rank_for_attempt,
    start_daily_attempt,
    todays_completed_attempts,
)


class TodayDailyChallengeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ensure_daily_unlocked(request.user)
        challenge = get_or_create_today_challenge()
        challenge = prefetch_challenge(challenge)
        data = DailyChallengeTodaySerializer(
            {
                'id': challenge.id,
                'date': challenge.date,
                'title': challenge.title,
                'total_questions': challenge.challenge_questions.count(),
                'already_attempted': DailyChallengeAttempt.objects.filter(
                    user=request.user,
                    challenge=challenge,
                ).exists(),
                'challenge_questions': challenge.challenge_questions.all(),
            }
        ).data
        return Response(data, status=status.HTTP_200_OK)


class StartDailyChallengeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        attempt = start_daily_attempt(request.user)
        attempt.challenge = prefetch_challenge(attempt.challenge)
        return Response(
            DailyStartSerializer(attempt).data,
            status=status.HTTP_201_CREATED,
        )


class SubmitDailyAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DailyAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question, is_correct = answer_daily_question(
            user=request.user,
            attempt_id=serializer.validated_data['attempt_id'],
            question_id=serializer.validated_data['question_id'],
            selected_index=serializer.validated_data['selected_index'],
            time_taken_seconds=serializer.validated_data.get('time_taken_seconds'),
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


class CompleteDailyChallengeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DailyCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attempt = complete_daily_attempt(
            user=request.user,
            attempt_id=serializer.validated_data['attempt_id'],
            time_taken_seconds=serializer.validated_data['time_taken_seconds'],
        )
        return Response(
            {
                'score': attempt.score,
                'total_questions': attempt.total_questions,
                'correct_answers': attempt.correct_answers,
                'wrong_answers': attempt.wrong_answers,
                'time_taken_seconds': attempt.time_taken_seconds,
                'rank_today': rank_for_attempt(attempt),
            },
            status=status.HTTP_200_OK,
        )


class DailyLeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ensure_daily_unlocked(request.user)
        data = [
            {'rank': index, **DailyLeaderboardSerializer(attempt).data}
            for index, attempt in enumerate(todays_completed_attempts(), start=1)
        ]
        return Response(data, status=status.HTTP_200_OK)


class DailyHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ensure_daily_unlocked(request.user)
        attempts = DailyChallengeAttempt.objects.select_related('challenge').filter(
            user=request.user,
        ).order_by('-challenge__date')[:30]
        serializer = DailyAttemptHistorySerializer(attempts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


def prefetch_challenge(challenge):
    return challenge.__class__.objects.prefetch_related(
        'challenge_questions__question',
    ).get(id=challenge.id)
