from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for creating a new user account."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        label='Confirm Password'
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',
            'password2',
            'avatar',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {'password': 'Passwords do not match.'}
            )
        return attrs

    def create(self, validated_data):
        # Remove password2 — not a real field
        validated_data.pop('password2')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            avatar=validated_data.get('avatar', 'scroll'),
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for login — returns user if credentials are valid."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs['username'],
            password=attrs['password']
        )
        if not user:
            raise serializers.ValidationError(
                {'detail': 'Invalid username or password.'}
            )
        if not user.is_active:
            raise serializers.ValidationError(
                {'detail': 'This account has been disabled.'}
            )
        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for reading and updating the current user's profile.
    Read-only fields like XP and streak cannot be edited by the user directly.
    """

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'avatar',
            'total_xp',
            'current_streak',
            'longest_streak',
            'last_played_date',
            'highest_level_unlocked',
            'has_unlocked_daily_challenge',
            'level_5_completed_at',
            'date_joined',
        ]
        read_only_fields = [
            'id',
            'total_xp',
            'current_streak',
            'longest_streak',
            'last_played_date',
            'highest_level_unlocked',
            'has_unlocked_daily_challenge',
            'level_5_completed_at',
            'date_joined',
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password while logged in."""

    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    new_password2 = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError(
                {'new_password': 'New passwords do not match.'}
            )
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
