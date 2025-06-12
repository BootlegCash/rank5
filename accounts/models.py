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
    profile = models.ForeignKey(Profile, related_name='daily_logs', on_delete=models.CASCADE)
    date = models.DateField()

    # --- ADD THESE FIELDS ---
    beer = models.PositiveIntegerField(default=0)
    floco = models.PositiveIntegerField(default=0)
    rum = models.PositiveIntegerField(default=0)
    whiskey = models.PositiveIntegerField(default=0)
    vodka = models.PositiveIntegerField(default=0)
    tequila = models.PositiveIntegerField(default=0)
    shotguns = models.PositiveIntegerField(default=0)
    snorkels = models.PositiveIntegerField(default=0)
    thrown_up = models.PositiveIntegerField(default=0) # To track negative points
    xp = models.IntegerField(default=0) # To store the XP for this log

    def __str__(self):
        return f"{self.profile.user.username} - {self.date}"

    def calculate_xp(self):
        """Calculates the total XP earned for the drinks in this log."""
        # These values should match the XP logic in your Flutter app
        drink_xp = (
            (self.beer * 355 * 0.05) +  # Standard beer ABV
            (self.floco * 355 * 0.15) + # Floco ABV
            (self.rum * 44 * 0.35) +    # Rum shot ABV
            (self.whiskey * 44 * 0.40) + # Whiskey shot ABV
            (self.vodka * 44 * 0.40) +   # Vodka shot ABV
            (self.tequila * 44 * 0.38)   # Tequila shot ABV
        )
        bonus_xp = (self.shotguns * 5) + (self.snorkels * 15)
        penalty_xp = self.thrown_up * 40

        total_xp = drink_xp + bonus_xp - penalty_xp
        return max(0, int(total_xp)) # Ensure XP doesn't go below zero

    def save(self, *args, **kwargs):
        # Recalculate XP every time the log is saved
        self.xp = self.calculate_xp()
        super().save(*args, **kwargs)

class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    profiles = models.ManyToManyField(Profile, related_name='achievements')

    def __str__(self):
        return self.name

# ✅ Your custom drink tracking helper
current_log_date = date.today()
