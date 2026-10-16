from django.db import models
from django.contrib.auth.models import User


class Batch(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    sugar_kg = models.FloatField()
    volume_l = models.FloatField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def potential_abv(self):
        # Simplified formula based on the Brewhaus calculator's logic:
        # roughly, sugar concentration translates to potential alcohol %.
        # (approx: 1kg sugar per 1L yields ~59% potential ABV by this simplified model
        if self.volume_l == 0:
            return 0
        sugar_concentration = self.sugar_kg / self.volume_l
        return round(sugar_concentration * 59, 2)

    def __str__(self):
        return f"{self.name} ({self.owner.username})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plaintext_password = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Profile for {self.user.username}"