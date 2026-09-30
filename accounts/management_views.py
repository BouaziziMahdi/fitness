from django.contrib import messages
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST


def manageable_users(actor):
    # Protect all privileged accounts, not merely members of a specific named group.
    return get_user_model().objects.filter(is_staff=False, is_superuser=False).exclude(pk=actor.pk).exclude(user_permissions__isnull=False).exclude(groups__permissions__isnull=False).order_by('username')


@login_required
@permission_required('accounts.manage_accounts', raise_exception=True)
def account_list(request):
    users = manageable_users(request.user)
    query = request.GET.get('q', '').strip()[:150]
    if query:
        users = users.filter(Q(username__icontains=query) | Q(email__icontains=query))
    return render(request, 'accounts/manage.html', {'page_obj': Paginator(users, 20).get_page(request.GET.get('page')), 'query': query})


@login_required
@permission_required('accounts.manage_accounts', raise_exception=True)
@require_POST
def change_access(request, pk):
    action = request.POST.get('action')
    if action not in ('activate', 'deactivate'):
        from django.http import HttpResponseBadRequest
        return HttpResponseBadRequest('Action inconnue.')
    with transaction.atomic():
        target = get_object_or_404(manageable_users(request.user).select_for_update(), pk=pk)
        active = action == 'activate'
        if target.is_active != active:
            target.is_active = active
            target.save(update_fields=['is_active'])
            LogEntry.objects.log_actions(user_id=request.user.pk, queryset=[target], action_flag=CHANGE, change_message=[{'changed': {'fields': ['Actif'], 'name': 'accès au compte', 'object': target.username}}])
    messages.success(request, f'Accès de {target.username} : {"activé" if active else "désactivé"}.')
    return redirect('manage_accounts')
