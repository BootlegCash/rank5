# accounts/serializers.py
from rest_framework import serializers
from .models import DailyLog

class DailyLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyLog
        # only the fields we need from the Flutter client
        fields = ['date', 'beer', 'floco', 'rum', 'whiskey', 'vodka', 'tequila',
                  'shotguns', 'snorkels', 'thrown_up']
        read_only_fields = ['date']