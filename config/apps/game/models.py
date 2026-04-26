import uuid
from django.db import models
from django.conf import settings
from apps.questions.models import Question


class GameSession(models.Model):
    """One complete quiz attempt by a user."""

    LEVEL_CHOICES = [(i, i) for i in range(1, 6)]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    difficulty_level = models.IntegerField(choices=LEVEL_CHOICES)
    questions = models.ManyToManyField(Question, through='SessionQuestion')

    # Scoring
    total_questions = models.IntegerField(default=10)
    correct_answers = models.IntegerField(default=0)
    xp_earned = models.IntegerField(default=0)
    time_taken_seconds = models.IntegerField(null=True)  # total session time

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    @property
    def score_percentage(self):
        if self.total_questions == 0:
            return 0
        return round((self.correct_answers / self.total_questions) * 100, 1)

    class Meta:
        db_table = 'game_sessions'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user} — Level {self.difficulty_level} — {self.score_percentage}%"


class SessionQuestion(models.Model):
    """Through model: tracks each question within a session + user's answer."""

    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.IntegerField()                        # Position in session (1-10)
    selected_index = models.IntegerField(null=True)      # What user chose (0-3), None if skipped
    is_correct = models.BooleanField(null=True)
    time_taken_seconds = models.IntegerField(null=True)  # Per-question time
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'session_questions'
        unique_together = [('session', 'question')]
        ordering = ['order']

    def __str__(self):
        return f"Session {self.session_id} — Q{self.order}"


class UserQuestionHistory(models.Model):
    """Permanent log of which questions a user has ever seen. Prevents repeats."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='question_history'
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    times_seen = models.IntegerField(default=1)
    times_correct = models.IntegerField(default=0)
    last_seen_at = models.DateTimeField(auto_now=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_question_history'
        unique_together = [('user', 'question')]
        indexes = [
            models.Index(fields=['user', 'question']),
        ]

    def __str__(self):
        return f"{self.user} — seen {self.times_seen}x"
