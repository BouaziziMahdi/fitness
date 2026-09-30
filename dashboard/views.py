from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .services import summary

@login_required
def dashboard(request):
    return render(request, 'dashboard.html', summary(request.user))
