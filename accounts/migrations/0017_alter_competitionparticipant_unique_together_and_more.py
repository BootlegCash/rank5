# Generated by Django 4.2.19 on 2025-04-23 03:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0016_competition_competitionparticipant_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='competitionparticipant',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='competitionparticipant',
            name='competition',
        ),
        migrations.RemoveField(
            model_name='competitionparticipant',
            name='profile',
        ),
        migrations.DeleteModel(
            name='Competition',
        ),
        migrations.DeleteModel(
            name='CompetitionParticipant',
        ),
    ]
