from rest_framework import serializers

from .models import DailyChallengeAttempt


class DailyQuestionSerializer(serializers.Serializer):
    id = serializers.UUIDField(source='question.id')
    order = serializers.IntegerField()
    question_text = serializers.CharField(source='question.question_text')
    options = serializers.JSONField(source='question.options')


class DailyChallengeTodaySerializer(serializers.Serializer):
    challenge_id = serializers.UUIDField(source='id')
    date = serializers.DateField()
    title = serializers.CharField()
    total_questions = serializers.IntegerField()
    already_attempted = serializers.BooleanField()
    questions = DailyQuestionSerializer(many=True, source='challenge_questions')


class DailyStartSerializer(serializers.Serializer):
    attempt_id = serializers.UUIDField(source='id')
    challenge_id = serializers.UUIDField(source='challenge.id')
    date = serializers.DateField(source='challenge.date')
    title = serializers.CharField(source='challenge.title')
    total_questions = serializers.IntegerField()
    questions = DailyQuestionSerializer(many=True, source='challenge.challenge_questions')


class DailyAnswerSerializer(serializers.Serializer):
    attempt_id = serializers.UUIDField()
    question_id = serializers.UUIDField()
    selected_index = serializers.IntegerField(min_value=0, max_value=3)
    time_taken_seconds = serializers.IntegerField(
        min_value=0,
        required=False,
        allow_null=True,
    )


class DailyCompleteSerializer(serializers.Serializer):
    attempt_id = serializers.UUIDField()
    time_taken_seconds = serializers.IntegerField(min_value=0)


class DailyAttemptHistorySerializer(serializers.ModelSerializer):
    challenge_id = serializers.UUIDField(source='challenge.id')
    date = serializers.DateField(source='challenge.date')
    title = serializers.CharField(source='challenge.title')

    class Meta:
        model = DailyChallengeAttempt
        fields = [
            'id',
            'challenge_id',
            'date',
            'title',
            'score',
            'total_questions',
            'correct_answers',
            'wrong_answers',
            'time_taken_seconds',
            'completed_at',
        ]


class DailyLeaderboardSerializer(serializers.Serializer):
    username = serializers.CharField(source='user.username')
    score = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    time_taken_seconds = serializers.IntegerField()
    completed_at = serializers.DateTimeField()
