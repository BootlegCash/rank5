from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    xp = models.IntegerField(default=0)
    rank = models.CharField(max_length=50, default='Bronze')
    total_alcohol = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

class FriendRequest(models.Model):
    from_user = models.ForeignKey(Profile, related_name='sent_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(Profile, related_name='received_requests', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_user.user.username} → {self.to_user.user.username}"

class Post(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(Profile, related_name='liked_posts', blank=True)

    def __str__(self):
        return f"Post by {self.user.user.username} at {self.timestamp}"

class DailyLog(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    date = models.DateField()
    # ✅ Uncomment if you plan to restore later
    # drink_count = models.IntegerField(default=0)
    # alcohol_ml = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.profile.user.username} - {self.date}"

class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    profiles = models.ManyToManyField(Profile, related_name='achievements')

    def __str__(self):
        return self.name

# ✅ Your custom drink tracking helper
current_log_date = date.today()