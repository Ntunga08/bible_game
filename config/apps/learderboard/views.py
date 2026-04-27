from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LeaderboardEntrySerializer, MyLeaderboardRankSerializer


User = get_user_model()
MAX_LIMIT = 100


class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = parse_limit(request.query_params.get('limit', 50))
        users = ranked_users()[:limit]
        serializer = LeaderboardEntrySerializer(
            [entry_for_user(user, index + 1) for index, user in enumerate(users)],
            many=True,
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class MyLeaderboardRankView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = ranked_users()
        total_players = len(users)
        rank = next(
            (
                index
                for index, user in enumerate(users, start=1)
                if user.id == request.user.id
            ),
            None,
        )
        data = entry_for_user(request.user, rank or total_players + 1)
        data['total_players'] = total_players
        serializer = MyLeaderboardRankSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


def ranked_users():
    return list(
        User.objects.order_by(
            '-total_xp',
            '-highest_level_unlocked',
            '-longest_streak',
            'date_joined',
        )
    )


def entry_for_user(user, rank):
    return {
        'rank': rank,
        'user_id': user.id,
        'username': user.username,
        'avatar': user.avatar,
        'total_xp': user.total_xp,
        'current_streak': user.current_streak,
        'highest_level_unlocked': user.highest_level_unlocked,
    }


def parse_limit(raw_limit):
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        limit = 50
    return max(1, min(limit, MAX_LIMIT))
