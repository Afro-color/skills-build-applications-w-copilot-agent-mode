from django.db import models
from django.contrib.auth.models import User

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