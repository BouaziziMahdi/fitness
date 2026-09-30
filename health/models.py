from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

def not_future(value):
    if value > timezone.localdate():
        raise ValidationError('La date ne peut pas être dans le futur.')

class Record(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField('date', default=timezone.localdate, validators=[not_future])
    class Meta:
        abstract = True
        ordering = ['-date', '-pk']

class WeightRecord(Record):
    weight = models.DecimalField('poids (kg)', max_digits=5, decimal_places=2, validators=[MinValueValidator(1), MaxValueValidator(500)])
    class Meta(Record.Meta):
        constraints = [models.UniqueConstraint(fields=['user', 'date'], name='one_weight_per_day')]

class Activity(Record):
    name = models.CharField('activité', max_length=150)
    duration = models.PositiveIntegerField('durée (minutes)', validators=[MinValueValidator(1), MaxValueValidator(1440)])
    calories_burned = models.PositiveIntegerField('calories brûlées (kcal)', validators=[MaxValueValidator(20000)])

class Meal(Record):
    name = models.CharField('repas', max_length=150)
    description = models.TextField('description', blank=True, max_length=2000)
    calories = models.PositiveIntegerField('calories (kcal)', validators=[MaxValueValidator(20000)])

class Goal(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    target_weight = models.DecimalField('poids cible (kg)', max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(500)])
    daily_calorie_target = models.PositiveIntegerField('objectif calorique quotidien (kcal)', null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(20000)])
    weekly_activity_target = models.PositiveSmallIntegerField('séances par semaine', null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(100)])

class Food(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField('aliment', max_length=120)
    kcal_per_100g = models.DecimalField('kcal pour 100 g (étiquette)', max_digits=6, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(1000)])
    class Meta:
        ordering = ['name']
    def __str__(self):
        return f'{self.name} ({self.kcal_per_100g} kcal / 100 g)'

class MealItem(models.Model):
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='items')
    food_name = models.CharField(max_length=120)
    kcal_per_100g = models.DecimalField(max_digits=6, decimal_places=2)
    grams = models.DecimalField(max_digits=7, decimal_places=2)
    @property
    def calories(self):
        return self.kcal_per_100g * self.grams / 100

class WeightReminder(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    enabled = models.BooleanField('Activer le rappel dans le dashboard', default=True)
    interval_days = models.PositiveSmallIntegerField('Rappeler après combien de jours sans mesure ?', default=7, validators=[MinValueValidator(1), MaxValueValidator(90)])
    snoozed_until = models.DateField(null=True, blank=True)

class PersonalGoal(models.Model):
    METRICS = [('sessions', 'Nombre de séances'), ('minutes', 'Minutes d’activité'), ('burned', 'Calories brûlées'), ('weighings', 'Nombre de mesures de poids')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField('nom de l’objectif', max_length=120)
    metric = models.CharField('indicateur', choices=METRICS, max_length=15)
    target = models.PositiveIntegerField('valeur à atteindre', validators=[MinValueValidator(1), MaxValueValidator(1000000)])
    start = models.DateField('début', default=timezone.localdate)
    end = models.DateField('échéance')
    class Meta:
        ordering = ['end', 'pk']
    def clean(self):
        if self.start and self.end and self.end < self.start:
            raise ValidationError({'end': 'L’échéance doit être postérieure ou égale au début.'})
