from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from .forms import RegisterForm, ProfileForm
from .models import Profile

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            user = form.save()
            Profile.objects.create(user=user)
        login(request, user)
        messages.success(request, 'Bienvenue ! Complétez votre profil pour commencer.')
        return redirect('profile')
    return render(request, 'form.html', {'form': form, 'title': 'Créer votre compte', 'subtitle': 'Votre progression commence ici.', 'button': 'Créer mon compte'})

@login_required
def profile(request):
    obj, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, instance=obj, initial={key: getattr(request.user, key) for key in ['first_name', 'last_name', 'email']})
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            form.save()
            for key in ['first_name', 'last_name', 'email']:
                setattr(request.user, key, form.cleaned_data[key])
            request.user.save(update_fields=['first_name', 'last_name', 'email'])
        messages.success(request, 'Profil mis à jour.')
        return redirect('profile')
    return render(request, 'form.html', {'form': form, 'title': 'Mon profil', 'subtitle': 'Les informations utiles à votre suivi.'})
