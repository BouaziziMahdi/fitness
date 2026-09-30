"""Descriptive statistics on recorded data; no clinical inference or prediction."""
from datetime import timedelta
from statistics import mean

from django.db.models import Sum
from django.utils import timezone

from health.models import Activity, Goal, Meal, WeightRecord


def analyze(user, today=None):
    today = today or timezone.localdate()
    start = today - timedelta(days=27)
    goal = Goal.objects.filter(user=user).first()
    weights = list(WeightRecord.objects.filter(user=user, date__range=(start, today)).order_by('date'))
    result = {'weight': None, 'nutrition': None, 'activity': None, 'messages': []}
    messages = result['messages']

    # Regress on elapsed days, not observation index: measurements may be irregular.
    if len(weights) >= 3 and (weights[-1].date - weights[0].date).days >= 7:
        x = [(row.date - weights[0].date).days for row in weights]
        y = [float(row.weight) for row in weights]
        xbar, ybar = mean(x), mean(y)
        slope = sum((a - xbar) * (b - ybar) for a, b in zip(x, y)) / sum((a - xbar) ** 2 for a in x)
        fitted = [ybar + slope * (a - xbar) for a in x]
        total = sum((b - ybar) ** 2 for b in y)
        r_squared = max(0, min(1, 1 - sum((b - f) ** 2 for b, f in zip(y, fitted)) / total)) if total else None
        stale = (today - weights[-1].date).days > 7
        weekly_slope = slope * 7
        result['weight'] = {'weekly_slope': round(weekly_slope, 2), 'count': len(weights), 'start': weights[0].date, 'end': weights[-1].date, 'r_squared': round(r_squared, 2) if r_squared is not None else None, 'stale': stale}
        messages.append(f'Sur {len(weights)} mesures, la tendance estimée du poids est de {weekly_slope:+.2f} kg par semaine. Elle décrit les saisies, sans prédire la suite.')
        if stale:
            messages.append('La dernière mesure date de plus de 7 jours. Ajoutez une mesure récente pour actualiser cette observation.')
        elif goal and goal.target_weight is not None:
            # Compare endpoints of fitted trend to avoid claiming progress after crossing a target.
            target = float(goal.target_weight)
            if abs(fitted[-1] - target) < abs(fitted[0] - target):
                messages.append('La tendance observée se rapproche de votre poids cible.')
            elif abs(fitted[-1] - target) > abs(fitted[0] - target):
                messages.append('La tendance observée s’éloigne de votre poids cible. Vérifiez vos saisies et la pertinence de votre objectif personnel.')
    else:
        messages.append('Pour estimer une tendance de poids, renseignez au moins 3 mesures couvrant 7 jours, dans les 28 derniers jours.')

    # Exclude the ongoing day and never treat missing meal logs as zero intake.
    end = today - timedelta(days=1)
    meal_start = today - timedelta(days=14)
    days = list(Meal.objects.filter(user=user, date__range=(meal_start, end)).values('date').annotate(total=Sum('calories')).order_by('date'))
    if days:
        average = round(mean(row['total'] for row in days))
        target = goal.daily_calorie_target if goal else None
        over = sum(row['total'] > target for row in days) if target else None
        result['nutrition'] = {'average': average, 'days': len(days), 'over_target': over, 'target': target, 'start': meal_start, 'end': end}
        messages.append(f'Moyenne des calories enregistrées : {average} kcal sur {len(days)} jour(s) renseigné(s) parmi les 14 jours précédents. Les jours sans repas sont exclus ; les journées renseignées peuvent être incomplètes.')
        if target:
            messages.append(f'Les saisies dépassent votre objectif calorique sur {over} des {len(days)} jours renseignés.')
    else:
        messages.append('Enregistrez vos repas pour comparer les calories saisies sur les 14 jours précédents.')

    # Compare two complete calendar weeks, so a partial week is not judged as a decline.
    monday = today - timedelta(days=today.weekday())
    previous_start, latest_start = monday - timedelta(days=14), monday - timedelta(days=7)
    previous = Activity.objects.filter(user=user, date__range=(previous_start, latest_start - timedelta(days=1))).count()
    latest_qs = Activity.objects.filter(user=user, date__range=(latest_start, monday - timedelta(days=1)))
    latest = latest_qs.count()
    if previous or latest:
        result['activity'] = {'previous': previous, 'latest': latest, 'delta': latest - previous, 'minutes': latest_qs.aggregate(total=Sum('duration'))['total'] or 0, 'start': latest_start, 'end': monday - timedelta(days=1)}
        messages.append(f'La dernière semaine complète compte {latest} séance(s) enregistrée(s), contre {previous} la semaine précédente. L’absence de saisie ne signifie pas forcément une absence d’activité.')
    return result
