from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, FriendRequest, Post, DailyLog

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

class StatsUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['xp', 'rank', 'total_alcohol']

class SendFriendRequestForm(forms.ModelForm):
    class Meta:
        model = FriendRequest
        fields = ['to_user']

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content']

# ✅ Fixed version of DailyLogForm
class DailyLogForm(forms.ModelForm):
    class Meta:
        model = DailyLog
        fields = ['date']   # ✅ ONLY fields that exist