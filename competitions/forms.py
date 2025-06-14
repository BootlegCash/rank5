from django import forms
from .models import Competition
from accounts.models import Profile


# competitions/forms.py
class CompetitionForm(forms.ModelForm):
    def __init__(self, *args, user_profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user_profile:
            # only allow choosing from your friends
            self.fields['participants'].queryset = user_profile.friends.all()

    class Meta:
        model = Competition
        fields = [
            'name',
            'start', 'end',
            'goal_beer', 'goal_floco', 'goal_rum',
            'goal_whiskey', 'goal_vodka', 'goal_tequila',
            'goal_alc_ml',
            'participants',
        ]
        widgets = {
            'start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end':   forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'participants': forms.CheckboxSelectMultiple,
        }
