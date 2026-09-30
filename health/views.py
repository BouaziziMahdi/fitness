from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from .models import WeightRecord, Activity, Meal, Goal
from .forms import WeightForm, ActivityForm, MealForm, GoalForm

KINDS = {'weights': (WeightRecord, WeightForm, 'Poids', 'une mesure'), 'activities': (Activity, ActivityForm, 'Activités', 'une activité'), 'meals': (Meal, MealForm, 'Repas', 'un repas')}

@login_required
def records(request, kind):
    model, _, title, label = KINDS[kind]
    queryset = model.objects.filter(user=request.user)
    if kind == 'meals':
        queryset = queryset.prefetch_related('items')
    page = Paginator(queryset, 20).get_page(request.GET.get('page'))
    return render(request, 'records.html', {'page_obj': page, 'kind': kind, 'title': title, 'label': label})

@login_required
def edit_record(request, kind, pk=None):
    model, form_class, _, label = KINDS[kind]
    obj = get_object_or_404(model, pk=pk, user=request.user) if pk else None
    form = form_class(request.POST or None, instance=obj, user=request.user)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            saved = form.save()
            if kind == 'meals':
                # A manual edit explicitly replaces ingredient-based calculation.
                saved.items.all().delete()
        messages.success(request, 'Enregistrement sauvegardé.')
        return redirect(kind)
    return render(request, 'form.html', {'form': form, 'title': ('Modifier ' if pk else 'Ajouter ') + label, 'subtitle': 'Modification manuelle : les calories saisies remplaceront le calcul et le détail des ingrédients.' if kind == 'meals' and obj and obj.items.exists() else ''})

@login_required
def delete_record(request, kind, pk):
    obj = get_object_or_404(KINDS[kind][0], pk=pk, user=request.user)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Enregistrement supprimé.')
        return redirect(kind)
    return render(request, 'confirm_delete.html', {'kind': kind, 'record': obj})

@login_required
def goals(request):
    obj, _ = Goal.objects.get_or_create(user=request.user)
    form = GoalForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Objectifs mis à jour.')
        return redirect('goals')
    return render(request, 'form.html', {'form': form, 'title': 'Mes objectifs', 'subtitle': 'Définissez vos repères personnels. Chaque objectif est facultatif.'})
