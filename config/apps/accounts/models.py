import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Extended user with game-specific fields."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    total_xp = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_played_date = models.DateField(null=True, blank=True)
    highest_level_unlocked = models.IntegerField(default=1)  # 1-5
    has_unlocked_daily_challenge = models.BooleanField(default=False)
    level_5_completed_at = models.DateTimeField(null=True, blank=True)
    avatar = models.CharField(max_length=100, default='scroll')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'
