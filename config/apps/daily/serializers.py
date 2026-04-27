from rest_framework import serializers

from apps.questions.serializers import PlayerQuestionSerializer

from .models import DailyChallenge, DailyChallengeAttempt


class DailyChallengeSerializer(serializers.ModelSerializer):
    questions = PlayerQuestionSerializer(many=True, read_only=True)
    completed = serializers.SerializerMethodField()
    attempt = serializers.SerializerMethodField()

    class Meta:
        model = DailyChallenge
        fields = ['id', 'date', 'theme', 'questions', 'completed', 'attempt']

    def get_completed(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and obj.attempts.filter(user=request.user).exists()
        )

    def get_attempt(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        attempt = obj.attempts.filter(user=request.user).first()
        if not attempt:
            return None
        return DailyChallengeAttemptSerializer(attempt).data


class DailyChallengeAttemptSerializer(serializers.ModelSerializer):
    date = serializers.DateField(source='challenge.date', read_only=True)
    theme = serializers.CharField(source='challenge.theme', read_only=True)

    class Meta:
        model = DailyChallengeAttempt
        fields = ['id', 'date', 'theme', 'score', 'xp_earned', 'completed_at']


class DailyAnswerItemSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    selected_index = serializers.IntegerField(min_value=0, max_value=3)


class DailySubmitSerializer(serializers.Serializer):
    answers = DailyAnswerItemSerializer(many=True)

    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError('Submit at least one answer.')

        question_ids = [item['question_id'] for item in value]
        if len(question_ids) != len(set(question_ids)):
            raise serializers.ValidationError('Duplicate question answers are not allowed.')
        return value
