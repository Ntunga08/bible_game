from rest_framework import serializers


class LeaderboardEntrySerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    user_id = serializers.UUIDField()
    username = serializers.CharField()
    avatar = serializers.CharField()
    total_xp = serializers.IntegerField()
    current_streak = serializers.IntegerField()
    highest_level_unlocked = serializers.IntegerField()


class MyLeaderboardRankSerializer(LeaderboardEntrySerializer):
    total_players = serializers.IntegerField()
