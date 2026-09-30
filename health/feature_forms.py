from decimal import Decimal
from django import forms
from django.forms import formset_factory
from .models import Food, WeightReminder, PersonalGoal, Meal
from .forms import RecordForm

class FoodForm(forms.ModelForm):
    class Meta:
        model = Food
        fields = ['name', 'kcal_per_100g']

class IngredientForm(forms.Form):
    food = forms.ModelChoiceField(label='Aliment', queryset=Food.objects.none())
    grams = forms.DecimalField(label='Quantité (g)', min_value=Decimal('0.01'), max_value=10000, max_digits=7, decimal_places=2)
    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['food'].queryset = Food.objects.filter(user=user)

Ingredients = formset_factory(IngredientForm, extra=3, min_num=1, validate_min=True, max_num=20, validate_max=True, absolute_max=20)

class CalculatedMealForm(RecordForm):
    class Meta:
        model = Meal
        fields = ['name', 'description', 'date']
        widgets = {'description': forms.Textarea(attrs={'rows': 2})}

class ReminderForm(forms.ModelForm):
    class Meta:
        model = WeightReminder
        fields = ['enabled', 'interval_days']

class PersonalGoalForm(forms.ModelForm):
    class Meta:
        model = PersonalGoal
        fields = ['title', 'metric', 'target', 'start', 'end']
        widgets = {field: forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}) for field in ['start', 'end']}
