import uuid
from django.db import models
from django.conf import settings
from apps.questions.models import Question


class DailyChallenge(models.Model):
    """A curated set of questions published daily for all users."""

    date = models.DateField(unique=True, db_index=True)
    questions = models.ManyToManyField(Question)
    theme = models.CharField(max_length=200, blank=True)  # e.g. "Miracles of Jesus"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'daily_challenges'
        ordering = ['-date']

    def __str__(self):
        return f"Daily Challenge — {self.date} — {self.theme or 'No theme'}"


class DailyChallengeAttempt(models.Model):
    """Records a user's attempt at the daily challenge."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='daily_attempts'
    )
    challenge = models.ForeignKey(
        DailyChallenge, on_delete=models.CASCADE, related_name='attempts'
    )
    score = models.IntegerField(default=0)
    xp_earned = models.IntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'daily_challenge_attempts'
        unique_together = [('user', 'challenge')]

    def __str__(self):
        return f"{self.user} — {self.challenge.date} — {self.score}/10"
