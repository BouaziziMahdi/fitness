from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Food, MealItem, WeightRecord, WeightReminder, PersonalGoal, Activity
from .feature_forms import FoodForm, Ingredients, CalculatedMealForm, ReminderForm, PersonalGoalForm


def reminder_status(user):
    settings = WeightReminder.objects.filter(user=user).first()
    today = timezone.localdate()
    if settings and (not settings.enabled or (settings.snoozed_until and settings.snoozed_until > today)):
        return None
    latest = WeightRecord.objects.filter(user=user, date__lte=today).first()
    interval = settings.interval_days if settings else 7
    due = latest.date + timedelta(days=interval) if latest else today
    return {'due': due, 'latest': latest.date if latest else None} if due <= today else None


def goal_progress(goal, today=None):
    today = today or timezone.localdate()
    until = min(today, goal.end)
    dates = {'user': goal.user, 'date__range': (goal.start, until)}
    if goal.metric == 'weighings':
        actual = WeightRecord.objects.filter(**dates).count()
    else:
        records = Activity.objects.filter(**dates)
        actual = records.count() if goal.metric == 'sessions' else records.aggregate(total=Sum('duration' if goal.metric == 'minutes' else 'calories_burned'))['total'] or 0
    return {'goal': goal, 'actual': actual, 'percent': min(100, round(actual * 100 / goal.target)), 'status': 'Atteint' if actual >= goal.target else ('À venir' if today < goal.start else ('Terminé' if today > goal.end else 'En cours'))}


@login_required
def foods(request):
    form = FoodForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.save()
        messages.success(request, 'Aliment ajouté à votre catalogue personnel.')
        return redirect('foods')
    return render(request, 'foods.html', {'form': form, 'foods': Food.objects.filter(user=request.user)})


@login_required
@require_POST
def delete_food(request, pk):
    get_object_or_404(Food, user=request.user, pk=pk).delete()
    return redirect('foods')


@login_required
def calculated_meal(request):
    form = CalculatedMealForm(request.POST or None, user=request.user)
    ingredients = Ingredients(request.POST or None, form_kwargs={'user': request.user})
    if request.method == 'POST':
        valid_form, valid_items = form.is_valid(), ingredients.is_valid()
        if valid_form and valid_items:
            rows = [row.cleaned_data for row in ingredients if row.cleaned_data]
            total = sum((row['food'].kcal_per_100g * row['grams'] / 100 for row in rows), Decimal(0)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            if total > 20000:
                form.add_error(None, 'Le total ne peut pas dépasser 20 000 kcal par repas.')
            else:
                with transaction.atomic():
                    meal = form.save(commit=False)
                    meal.calories = int(total)
                    meal.save()
                    MealItem.objects.bulk_create([MealItem(meal=meal, food_name=row['food'].name, kcal_per_100g=row['food'].kcal_per_100g, grams=row['grams']) for row in rows])
                messages.success(request, f'Repas enregistré : {meal.calories} kcal calculées.')
                return redirect('meals')
    return render(request, 'calculated_meal.html', {'form': form, 'ingredients': ingredients})


@login_required
def reminders(request):
    obj, _ = WeightReminder.objects.get_or_create(user=request.user)
    form = ReminderForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.snoozed_until = None
        obj.save()
        messages.success(request, 'Préférences de rappel enregistrées.')
        return redirect('dashboard')
    return render(request, 'form.html', {'form': form, 'title': 'Rappels de poids', 'subtitle': 'Rappel dans le dashboard lors de vos visites. Aucun email ni notification externe.'})


@login_required
@require_POST
def snooze(request):
    obj, _ = WeightReminder.objects.get_or_create(user=request.user)
    obj.snoozed_until = timezone.localdate() + timedelta(days=1)
    obj.save(update_fields=['snoozed_until'])
    return redirect('dashboard')


@login_required
def personal_goals(request):
    return render(request, 'personal_goals.html', {'goals': [goal_progress(g) for g in PersonalGoal.objects.filter(user=request.user)]})


@login_required
def edit_goal(request, pk=None):
    obj = get_object_or_404(PersonalGoal, pk=pk, user=request.user) if pk else None
    form = PersonalGoalForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        goal = form.save(commit=False)
        goal.user = request.user
        goal.save()
        return redirect('personal_goals')
    return render(request, 'form.html', {'form': form, 'title': 'Objectif personnalisé', 'subtitle': 'Choisissez un indicateur, une valeur et une période. La progression se calcule depuis votre journal.'})


@login_required
@require_POST
def delete_goal(request, pk):
    get_object_or_404(PersonalGoal, user=request.user, pk=pk).delete()
    return redirect('personal_goals')
