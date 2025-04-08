from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils.timezone import now
from django.db.models import Count
from datetime import timedelta

SEASONS = [
    ('spring', 'Spring'),
    ('summer', 'Summer'),
    ('autumn', 'Autumn'),
    ('winter', 'Winter')
]

class Streak(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='streak')
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Streak"

class Badge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    name = models.CharField(max_length=100)
    description = models.TextField()
    earned_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} Badge for {self.user.username}"

class WeightLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    weight = models.FloatField()
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.weight}kg on {self.date}"

class Achievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    date_achieved = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class BadgeTier(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    level = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    def __str__(self):
        return f"Tier {self.level}: {self.name}"

class PurchasableBadge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tier = models.ForeignKey(BadgeTier, on_delete=models.CASCADE, related_name='badges')
    icon = models.ImageField(upload_to='badges/')
    season = models.CharField(max_length=10, choices=SEASONS, default='spring')

    def __str__(self):
        return f"{self.name} (Tier {self.tier.level})"

    def is_current_season(self):
        current_month = now().month
        if 3 <= current_month <= 5:
            return self.season == 'spring'
        elif 6 <= current_month <= 8:
            return self.season == 'summer'
        elif 9 <= current_month <= 11:
            return self.season == 'autumn'
        else:
            return self.season == 'winter'

class DailyBadgeLimit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_badge_limits')
    date = models.DateField(auto_now_add=True)
    badge_count = models.PositiveIntegerField(default=0)

    def can_award_badge(self):
        return self.badge_count < 2

    def increment_badge_count(self):
        if self.can_award_badge():
            self.badge_count += 1
            self.save()
            return True
        return False

class WeeklyBadgePurchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_badge_purchases')
    badge = models.ForeignKey(PurchasableBadge, on_delete=models.CASCADE)
    purchase_date = models.DateField(auto_now_add=True)

    @staticmethod
    def can_purchase_badge(user):
        start_of_week = now().date() - timedelta(days=now().date().weekday())
        end_of_week = start_of_week + timedelta(days=6)
        weekly_count = WeeklyBadgePurchase.objects.filter(user=user, purchase_date__range=(start_of_week, end_of_week)).count()
        return weekly_count < 5