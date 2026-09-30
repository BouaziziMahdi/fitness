from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import User, Group, Permission
from django.test import TestCase, Client
from django.urls import reverse
from health.models import Meal


class AccountRoleTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user('manager')
        self.manager.groups.add(Group.objects.get(name='Responsables des comptes'))
        self.user = User.objects.create_user('ordinary')
        self.admin = User.objects.create_superuser('administrator', '', 'Test-123456!')
        self.client.force_login(self.manager)

    def url(self, user=None):
        return reverse('change_account_access', args=[(user or self.user).pk])

    def test_manager_can_change_access_with_audit(self):
        self.assertContains(self.client.get(reverse('manage_accounts')), 'ordinary')
        session = Client()
        session.force_login(self.user)
        response = self.client.post(self.url(), {'action': 'deactivate'})
        self.assertRedirects(response, reverse('manage_accounts'))
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertEqual(session.get(reverse('dashboard')).status_code, 302)
        self.assertEqual(LogEntry.objects.filter(user=self.manager).count(), 1)
        self.client.post(self.url(), {'action': 'activate'})
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_manager_cannot_modify_privileged_accounts_or_self(self):
        staff = User.objects.create_user('staff', is_staff=True)
        privileged = User.objects.create_user('privileged')
        privileged.user_permissions.add(Permission.objects.get(codename='view_user'))
        for target in [self.admin, self.manager, staff, privileged]:
            self.assertEqual(self.client.post(self.url(target), {'action': 'deactivate'}).status_code, 404)
        self.assertEqual(self.client.get('/admin/auth/user/').status_code, 302)
        self.client.post(self.url(), {'action': 'activate', 'is_superuser': True, 'is_staff': True})
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_staff)

    def test_manager_cannot_view_health_data(self):
        meal = Meal.objects.create(user=self.user, name='Confidentiel', calories=400)
        self.assertNotContains(self.client.get(reverse('meals')), 'Confidentiel')
        self.assertEqual(self.client.get(reverse('meals_edit', args=[meal.pk])).status_code, 404)

    def test_standard_user_cannot_manage_accounts(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('manage_accounts')).status_code, 403)
        self.assertEqual(self.client.post(self.url(self.manager), {'action': 'deactivate'}).status_code, 403)

    def test_revoked_role_takes_effect(self):
        self.manager.groups.clear()
        self.assertEqual(self.client.get(reverse('manage_accounts')).status_code, 403)

    def test_post_and_csrf_required(self):
        self.assertEqual(self.client.get(self.url()).status_code, 405)
        self.assertEqual(self.client.post(self.url(), {'action': 'invalid'}).status_code, 400)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.manager)
        self.assertEqual(client.post(self.url(), {'action': 'deactivate'}).status_code, 403)
