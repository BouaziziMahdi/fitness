from datetime import timedelta
from .analytics import analyze
from health.features import reminder_status
from django.db.models import Sum
from django.utils import timezone
from accounts.models import Profile
from health.models import WeightRecord, Activity, Meal, Goal

def summary(user):
    today = timezone.localdate()
    weights = list(WeightRecord.objects.filter(user=user, date__lte=today).order_by('date', 'pk'))
    profile = Profile.objects.filter(user=user).first()
    goal = Goal.objects.filter(user=user).first()
    current = weights[-1].weight if weights else None
    target = goal.target_weight if goal else None
    bmi = round(float(current) / (float(profile.height) / 100) ** 2, 1) if current and profile and profile.height else None
    consumed = Meal.objects.filter(user=user, date=today).aggregate(total=Sum('calories'))['total'] or 0
    burned = Activity.objects.filter(user=user, date=today).aggregate(total=Sum('calories_burned'))['total'] or 0
    weekly = Activity.objects.filter(user=user, date__range=(today - timedelta(days=today.weekday()), today))
    count = weekly.count()
    totals = weekly.aggregate(minutes=Sum('duration'), calories=Sum('calories_burned'))
    progress = None
    if current is not None and target is not None:
        start = weights[0].weight
        progress = (100 if current == target else 0) if start == target else max(0, min(100, round(float((current - start) / (target - start)) * 100)))
    delta = current - weights[-2].weight if len(weights) > 1 else None
    bmi_delta = round(float(delta) / (float(profile.height) / 100) ** 2, 1) if delta is not None and bmi is not None else None
    notes = []
    if not weights:
        notes.append('Ajoutez votre première mesure de poids pour démarrer votre suivi.')
    if not profile or not profile.height:
        notes.append('Renseignez votre taille dans le profil pour afficher votre IMC.')
    if len(weights) > 1 and target is not None and abs(current - target) < abs(weights[-2].weight - target):
        notes.append('Votre poids évolue dans la direction de votre objectif.')
    if goal and goal.daily_calorie_target and consumed > goal.daily_calorie_target:
        notes.append('Votre consommation calorique dépasse votre objectif du jour.')
    if goal and goal.weekly_activity_target:
        notes.append('Votre objectif hebdomadaire d’activité est atteint.' if count >= goal.weekly_activity_target else f'{count} séance(s) enregistrée(s) sur {goal.weekly_activity_target} cette semaine. La semaine est en cours.')
    if not notes:
        notes.append('Continuez à renseigner votre journal pour observer vos tendances.')
    return {'weight_reminder': reminder_status(user), 'analysis': analyze(user, today), 'today': today, 'current': current, 'target': target, 'bmi': bmi, 'bmi_delta': bmi_delta, 'consumed': consumed, 'burned': burned, 'count': count, 'minutes': totals['minutes'] or 0, 'weekly_burned': totals['calories'] or 0, 'progress': progress, 'delta': delta, 'goal': goal, 'notes': notes, 'chart': [{'date': w.date.isoformat(), 'weight': float(w.weight)} for w in weights], 'recent_meals': Meal.objects.filter(user=user, date=today)[:5]}
