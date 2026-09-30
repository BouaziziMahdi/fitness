from django.contrib import admin
from .models import WeightRecord, Activity, Meal, Goal
for model in [WeightRecord, Activity, Meal, Goal]:
    admin.site.register(model)
