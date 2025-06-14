# competitions/models.py

from django.db import models
from django.utils import timezone
from accounts.models import Profile, DailyLog

class Competition(models.Model):
    name         = models.CharField(max_length=100)
    created_by   = models.ForeignKey(
        Profile,
        related_name='created_competitions',
        on_delete=models.CASCADE
    )
    participants = models.ManyToManyField(
        Profile,
        through='CompetitionParticipant',
        related_name='competitions'
    )
    start        = models.DateTimeField(default=timezone.now)
    end          = models.DateTimeField()

    goal_beer     = models.PositiveIntegerField(null=True, blank=True)
    goal_floco    = models.PositiveIntegerField(null=True, blank=True)
    goal_rum      = models.PositiveIntegerField(null=True, blank=True)
    goal_whiskey  = models.PositiveIntegerField(null=True, blank=True)
    goal_vodka    = models.PositiveIntegerField(null=True, blank=True)
    goal_tequila  = models.PositiveIntegerField(null=True, blank=True)
    goal_alc_ml   = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-start']   # Always fetch newest first

    def __str__(self):
        return f"{self.name} ({self.start.date()}→{self.end.date()})"

    def leaderboard(self):
        """
        Returns a list of dicts { profile, total_alc } sorted by total alcohol consumed
        during the competition period.
        """
        entries = []
        logs = DailyLog.objects.filter(
            date__gte=self.start.date(),
            date__lte=self.end.date(),
            profile__in=self.participants.all()
        )
        for profile in self.participants.all():
            total = sum(
                l.calculate_alcohol_drank()
                for l in logs if l.profile == profile
            )
            entries.append({'profile': profile, 'total_alc': total})
        return sorted(entries, key=lambda e: e['total_alc'], reverse=True)

    def _totals(self):
        """
        Helper: returns a dict mapping each participant Profile → total_ml consumed
        during the competition period.
        """
        totals = {p: 0 for p in self.participants.all()}
        logs = DailyLog.objects.filter(
            date__gte=self.start.date(),
            date__lte=self.end.date(),
            profile__in=totals.keys()
        )
        for log in logs:
            totals[log.profile] += log.calculate_alcohol_drank()
        return totals

    def winner(self):
        """
        Determine the winner Profile:
        - If goal_alc_ml is set and reached, winner is max among those ≥ goal.
        - Otherwise, winner is the max total overall.
        Returns None if no participants.
        """
        totals = self._totals()
        if self.goal_alc_ml:
            reached = {p: t for p, t in totals.items() if t >= self.goal_alc_ml}
            if reached:
                return max(reached, key=lambda p: reached[p])
        if totals:
            return max(totals, key=lambda p: totals[p])
        return None

    def stop_if_goal_reached(self):
        """
        If the competition is still active and any participant has reached the goal,
        sets end to now and saves (thus marking it ended).
        """
        if self.goal_alc_ml and self.is_active:
            for total in self._totals().values():
                if total >= self.goal_alc_ml:
                    self.end = timezone.now()
                    self.save()
                    break

    @property
    def is_active(self):
        now = timezone.localtime(timezone.now())
        return self.start <= now <= self.end


class CompetitionParticipant(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE)
    profile     = models.ForeignKey(Profile,     on_delete=models.CASCADE)
    joined_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('competition', 'profile')

    def __str__(self):
        return f"{self.profile.user.username} in {self.competition.name}"
