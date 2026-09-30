from django import forms
from .models import WeightRecord, Activity, Meal, Goal

class RecordForm(forms.ModelForm):
    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.user = user
        self.fields['date'].widget = forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})
    def clean(self):
        data = super().clean()
        if isinstance(self.instance, WeightRecord) and data.get('date') and WeightRecord.objects.filter(user=self.instance.user, date=data['date']).exclude(pk=self.instance.pk).exists():
            self.add_error('date', 'Une mesure existe déjà pour cette date. Modifiez-la depuis votre historique.')
        return data

class WeightForm(RecordForm):
    class Meta:
        model = WeightRecord
        fields = ['weight', 'date']

class ActivityForm(RecordForm):
    class Meta:
        model = Activity
        fields = ['name', 'duration', 'calories_burned', 'date']

class MealForm(RecordForm):
    class Meta:
        model = Meal
        fields = ['name', 'description', 'calories', 'date']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['target_weight', 'daily_calorie_target', 'weekly_activity_target']
