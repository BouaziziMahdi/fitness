"""Account-management permissions are separate from access to health data."""
MANAGER_GROUP = 'Responsables des comptes'


def can_manage_accounts(user):
    return user.is_authenticated and user.is_active and user.has_perm('accounts.manage_accounts')


def role_context(request):
    user = request.user
    manager = can_manage_accounts(user)
    role = 'Administrateur' if user.is_authenticated and user.is_superuser else ('Responsable des comptes' if manager else 'Utilisateur')
    return {'can_manage_accounts': manager, 'account_role': role}
