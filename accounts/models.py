from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    age = models.PositiveSmallIntegerField('âge', null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(120)])
    height = models.DecimalField('taille (cm)', max_digits=5, decimal_places=1, null=True, blank=True, validators=[MinValueValidator(30), MaxValueValidator(260)])
    class Meta:
        permissions = [('manage_accounts', 'Peut activer ou désactiver les comptes ordinaires')]

    def __str__(self):
        return str(self.user)
