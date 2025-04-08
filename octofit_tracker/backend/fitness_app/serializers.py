from rest_framework import serializers
from .models import WeightLog, Achievement, UserProfile, BadgeTier, PurchasableBadge

class WeightLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeightLog
        fields = ['id', 'weight', 'date']

class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ['id', 'title', 'description', 'date_achieved']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'avatar', 'bio']

class BadgeTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = BadgeTier
        fields = ['id', 'name', 'description', 'level']

class PurchasableBadgeSerializer(serializers.ModelSerializer):
    tier = BadgeTierSerializer()

    class Meta:
        model = PurchasableBadge
        fields = ['id', 'name', 'description', 'price', 'tier', 'icon']