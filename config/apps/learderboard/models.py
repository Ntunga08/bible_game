from django.db import models
from django.conf import settings


class Leaderboard(models.Model):
    """Cached weekly/all-time leaderboard snapshots."""

    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('alltime', 'All Time'),
    ]

    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leaderboard_entries'
    )
    rank = models.IntegerField()
    xp = models.IntegerField()
    correct_answers = models.IntegerField(default=0)
    sessions_played = models.IntegerField(default=0)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leaderboard'
        unique_together = [('period', 'user')]
        ordering = ['period', 'rank']

    def __str__(self):
        return f"[{self.period.upper()}] #{self.rank} — {self.user}"