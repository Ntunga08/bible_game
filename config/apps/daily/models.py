import uuid
from django.db import models
from django.conf import settings
from apps.questions.models import Question


class DailyChallenge(models.Model):
    """A curated set of questions published daily for all users."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(unique=True, db_index=True)
    title = models.CharField(max_length=200, default='Daily Master Challenge')
    questions = models.ManyToManyField(Question, through='DailyChallengeQuestion')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'daily_challenges'
        ordering = ['-date']

    def __str__(self):
        return f"Daily Challenge — {self.date} — {self.title}"


class DailyChallengeQuestion(models.Model):
    """Ordered question list for a daily challenge."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(
        DailyChallenge,
        on_delete=models.CASCADE,
        related_name='challenge_questions',
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        db_table = 'daily_challenge_questions'
        unique_together = [('challenge', 'question')]
        ordering = ['order']

    def __str__(self):
        return f"{self.challenge.date} — Q{self.order}"


class DailyChallengeAttempt(models.Model):
    """Records a user's attempt at the daily challenge."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='daily_attempts'
    )
    challenge = models.ForeignKey(
        DailyChallenge, on_delete=models.CASCADE, related_name='attempts'
    )
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=15)
    correct_answers = models.IntegerField(default=0)
    wrong_answers = models.IntegerField(default=0)
    time_taken_seconds = models.IntegerField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'daily_challenge_attempts'
        unique_together = [('user', 'challenge')]

    def __str__(self):
        return f"{self.user} — {self.challenge.date} — {self.score}/15"


class DailyChallengeAnswer(models.Model):
    """Stores one answer inside a daily challenge attempt."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(
        DailyChallengeAttempt,
        on_delete=models.CASCADE,
        related_name='answers',
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_index = models.IntegerField()
    is_correct = models.BooleanField()
    time_taken_seconds = models.IntegerField(null=True, blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'daily_challenge_answers'
        unique_together = [('attempt', 'question')]

    def __str__(self):
        return f"{self.attempt_id} — {self.question_id}"
