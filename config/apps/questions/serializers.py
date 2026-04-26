from rest_framework import serializers

from .models import Category, Question


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'display_name', 'icon']


class QuestionSerializer(serializers.ModelSerializer):
    correct_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = Question
        fields = [
            'id',
            'question_text',
            'options',
            'correct_index',
            'explanation',
            'bible_reference',
            'full_verse_text',
            'difficulty',
            'testament',
            'category',
            'cognitive_type',
            'topic_tags',
            'book_name',
            'status',
            'quality_score',
            'ai_generated',
            'times_served',
            'times_correct',
            'times_incorrect',
            'correct_rate',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'times_served',
            'times_correct',
            'times_incorrect',
            'correct_rate',
            'created_at',
            'updated_at',
        ]

    def validate_options(self, value):
        if not isinstance(value, list) or len(value) != 4:
            raise serializers.ValidationError('Options must be a list of 4 answers.')
        if not all(isinstance(option, str) and option.strip() for option in value):
            raise serializers.ValidationError('Each option must be a non-empty string.')
        return value

    def validate_correct_index(self, value):
        if value not in range(4):
            raise serializers.ValidationError('Correct index must be between 0 and 3.')
        return value

    def validate_quality_score(self, value):
        if value < 0 or value > 5:
            raise serializers.ValidationError('Quality score must be between 0 and 5.')
        return value


class PlayerQuestionSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Question
        fields = [
            'id',
            'question_text',
            'options',
            'bible_reference',
            'full_verse_text',
            'difficulty',
            'testament',
            'category',
            'cognitive_type',
            'topic_tags',
            'book_name',
        ]


class CheckAnswerSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    selected_index = serializers.IntegerField(min_value=0, max_value=3)

    def validate_question_id(self, value):
        try:
            question = Question.objects.get(id=value, status='approved')
        except Question.DoesNotExist as exc:
            raise serializers.ValidationError('Approved question not found.') from exc
        self.context['question'] = question
        return value
