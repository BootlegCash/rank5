from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
from .models import Post
import re


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    display_name = forms.CharField(required=True, max_length=15, label="Display Name")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'display_name',) # Add display_name here if you want it part of UserCreationForm.Meta.fields handling, or handle it in save()

    def clean_display_name(self):
        display_name = self.cleaned_data.get('display_name')
        if not re.match(r"^[a-zA-Z]+$", display_name):
            raise forms.ValidationError("Display name must contain only letters.")
        # Add profanity/reserved word checks here (see point 3)
        # Example for reserved names:
        RESERVED_NAMES = ['admin', 'user', 'moderator', 'root'] # Expand this list
        if display_name.lower() in RESERVED_NAMES:
            raise forms.ValidationError("This display name is reserved.")
        # Add profanity check here
        return display_name

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Add profanity/reserved word checks here for username
        RESERVED_USERNAMES = ['admin', 'user', 'moderator', 'root', 'superuser'] # Expand
        if username.lower() in RESERVED_USERNAMES:
            raise forms.ValidationError("This username is reserved.")
        # Add profanity check here
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        # UserCreationForm usually saves the user if commit=True.
        # We need to ensure the user is saved before we can create/update the profile.
        if commit:
            user.save()
            # Save display_name to the Profile
            # Profile is created via a signal in your accounts/models.py, so we update it.
            profile, created = Profile.objects.get_or_create(user=user)
            profile.display_name = self.cleaned_data.get('display_name')
            profile.save()
        return user

class StatsUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vodka'].label = "vodka (40%)"
        self.fields['tequila'].label = "tequila (50%)"
        self.fields['whiskey'].label = "whiskey (30%)"
        self.fields['rum'].label = "rum (20%)"
        self.fields['floco'].label = "floco (13%) (12 oz)"
        self.fields['beer'].label = "beer/seltzer (5%) (12oz)"
        
        
        
    class Meta:
        model = Profile
        fields = [
            'beer', 'floco', 'rum', 'whiskey', 'vodka', 'tequila',
            'shotguns', 'snorkels', 'thrown_up'
        ]

class SendFriendRequestForm(forms.Form):
    username = forms.CharField(label="Friend's Username", max_length=150)

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'placeholder': "What's happening in your night?",
                'maxlength': '280'
            })
        }

class DailyLogForm(forms.Form):
    beer = forms.IntegerField(min_value=0, initial=0, label="Beers/Seltzers")
    floco = forms.IntegerField(min_value=0, initial=0, label="Flocos")
    rum = forms.IntegerField(min_value=0, initial=0, label="Rum Shots")
    whiskey = forms.IntegerField(min_value=0, initial=0, label="Whiskey Shots")
    vodka = forms.IntegerField(min_value=0, initial=0, label="Vodka Shots")
    tequila = forms.IntegerField(min_value=0, initial=0, label="Tequila Shots")
    shotguns = forms.IntegerField(min_value=0, initial=0, label="Shotguns")
    snorkels = forms.IntegerField(min_value=0, initial=0, label="Snorkels")
    thrown_up = forms.IntegerField(min_value=0, initial=0, label="Times Thrown Up")


