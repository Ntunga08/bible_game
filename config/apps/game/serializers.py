from rest_framework import serializers

from .models import GameSession, SessionQuestion


class GameSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameSession
        fields = [
            'id',
            'current_level',
            'score',
            'total_questions',
            'correct_answers',
            'status',
            'started_at',
            'ended_at',
        ]
        read_only_fields = fields


class StartGameSerializer(serializers.ModelSerializer):
    session_id = serializers.UUIDField(source='id', read_only=True)

    class Meta:
        model = GameSession
        fields = ['session_id', 'current_level']


class GameQuestionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='question.id', read_only=True)
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    options = serializers.JSONField(source='question.options', read_only=True)

    class Meta:
        model = SessionQuestion
        fields = ['id', 'question_text', 'options']


class SubmitAnswerSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    question_id = serializers.UUIDField()
    selected_index = serializers.IntegerField(min_value=0, max_value=3)


class AnswerResultSerializer(serializers.Serializer):
    is_correct = serializers.BooleanField()
    correct_index = serializers.IntegerField()
    explanation = serializers.CharField()
    bible_reference = serializers.CharField()


class CompleteLevelSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['passed', 'failed'])
    next_level = serializers.IntegerField(allow_null=True)
