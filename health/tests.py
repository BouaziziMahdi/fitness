from datetime import timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from accounts.models import Profile
from .models import WeightRecord, Activity, Meal, Goal
from dashboard.services import summary

class FitnessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', password='Testing-Strong-123', email='alice@example.com')
        self.other = User.objects.create_user('bob', password='Testing-Strong-123')
        self.client.force_login(self.user)
        self.today = timezone.localdate()

    def test_private_pages_and_admin(self):
        anon = Client()
        for name in ['dashboard', 'profile', 'weights', 'activities', 'meals', 'goals']:
            self.assertEqual(anon.get(reverse(name)).status_code, 302)
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.assertEqual(self.client.get('/admin/').status_code, 302)

    def test_registration_and_profile(self):
        self.client.logout()
        response = self.client.post(reverse('register'), {'username': 'charlie', 'email': 'c@example.com', 'password1': 'Testing-Strong-123', 'password2': 'Testing-Strong-123'})
        self.assertRedirects(response, reverse('profile'))
        user = User.objects.get(username='charlie')
        self.assertTrue(user.check_password('Testing-Strong-123'))
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.client.post(reverse('profile'), {'first_name': 'Charles', 'last_name': 'Test', 'email': 'c@example.com', 'age': 30, 'height': 180})
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Charles')
        self.assertEqual(user.profile.height, Decimal('180'))

    def test_inactive_account(self):
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 302)
        self.assertFalse(self.client.login(username='alice', password='Testing-Strong-123'))

    def test_user_isolation_and_crud(self):
        for kind, model, fields in [('weights', WeightRecord, {'weight': '75.20'}), ('activities', Activity, {'name': 'Course privée', 'duration': 30, 'calories_burned': 200}), ('meals', Meal, {'name': 'Repas privé', 'description': 'Secret', 'calories': 300})]:
            foreign = model.objects.create(user=self.other, date=self.today, **fields)
            for action in ['edit', 'delete']:
                url = reverse(kind+'_'+action, args=[foreign.pk])
                self.assertEqual(self.client.get(url).status_code, 404)
                self.assertEqual(self.client.post(url, fields).status_code, 404)
            response = self.client.post(reverse(kind+'_add'), {**fields, 'date': self.today.isoformat(), 'user': self.other.pk})
            self.assertRedirects(response, reverse(kind))
            own = model.objects.get(user=self.user)
            self.assertContains(self.client.get(reverse(kind+'_edit', args=[own.pk])), '<form')
            self.client.post(reverse(kind+'_edit', args=[own.pk]), {**fields, 'date': self.today.isoformat()})
            self.assertEqual(model.objects.filter(user=self.user).count(), 1)
            self.client.get(reverse(kind+'_delete', args=[own.pk]))
            self.assertTrue(model.objects.filter(pk=own.pk).exists())
            self.client.post(reverse(kind+'_delete', args=[own.pk]))
            self.assertFalse(model.objects.filter(pk=own.pk).exists())
            self.assertTrue(model.objects.filter(pk=foreign.pk).exists())

    def test_invalid_and_duplicate_measure(self):
        url = reverse('weights_add')
        for weight, date in [('-2', self.today), ('75', self.today+timedelta(days=1))]:
            response = self.client.post(url, {'weight': weight, 'date': date.isoformat()})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['form'].errors)
        self.assertFalse(WeightRecord.objects.exists())
        self.client.post(url, {'weight': 75, 'date': self.today.isoformat()})
        response = self.client.post(url, {'weight': 76, 'date': self.today.isoformat()})
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(WeightRecord.objects.count(), 1)

    def test_dashboard_calculations_and_scope(self):
        Profile.objects.create(user=self.user, height=180)
        Goal.objects.create(user=self.user, target_weight=72, daily_calorie_target=1800, weekly_activity_target=4)
        WeightRecord.objects.create(user=self.user, weight=78, date=self.today-timedelta(days=7))
        WeightRecord.objects.create(user=self.user, weight=75, date=self.today)
        Meal.objects.create(user=self.user, name='Midi', calories=1900, date=self.today)
        Meal.objects.create(user=self.user, name='Hier', calories=999, date=self.today-timedelta(days=1))
        Meal.objects.create(user=self.other, name='Autre', calories=999, date=self.today)
        Activity.objects.create(user=self.user, name='Marche', duration=30, calories_burned=150, date=self.today)
        Activity.objects.create(user=self.user, name='Ancienne', duration=90, calories_burned=900, date=self.today-timedelta(days=7))
        data = summary(self.user)
        self.assertEqual(data['bmi'], 23.1)
        self.assertEqual(data['progress'], 50)
        self.assertEqual(data['delta'], -3)
        self.assertEqual(data['consumed'], 1900)
        self.assertEqual(data['burned'], 150)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['minutes'], 30)
        self.assertEqual(len(data['notes']), 3)
        self.assertContains(self.client.get(reverse('dashboard')), 'weight-data')

    def test_weight_gain_and_equal_target(self):
        WeightRecord.objects.create(user=self.user, weight=60, date=self.today-timedelta(days=1))
        record = WeightRecord.objects.create(user=self.user, weight=65, date=self.today)
        goal = Goal.objects.create(user=self.user, target_weight=70)
        self.assertEqual(summary(self.user)['progress'], 50)
        goal.target_weight = 60
        goal.save()
        self.assertEqual(summary(self.user)['progress'], 0)
        record.weight = 60
        record.save()
        self.assertEqual(summary(self.user)['progress'], 100)

    def test_csrf_and_logout(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(reverse('weights_add'), {'weight': 70, 'date': self.today}).status_code, 403)
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.assertRedirects(self.client.post(reverse('logout')), reverse('login'))

    def test_user_deletion_cascades(self):
        Profile.objects.create(user=self.user)
        Goal.objects.create(user=self.user)
        WeightRecord.objects.create(user=self.user, weight=75)
        Activity.objects.create(user=self.user, name='Marche', duration=30, calories_burned=100)
        Meal.objects.create(user=self.user, name='Midi', calories=600)
        self.user.delete()
        for model in [Profile, Goal, WeightRecord, Activity, Meal]:
            self.assertEqual(model.objects.count(), 0)

    def test_goal_validation(self):
        response = self.client.post(reverse('goals'), {'daily_calorie_target': -1, 'weekly_activity_target': 0})
        self.assertTrue(response.context['form'].errors)
        self.client.post(reverse('goals'), {'target_weight': 70, 'daily_calorie_target': 2000, 'weekly_activity_target': 3})
        self.assertEqual(Goal.objects.get(user=self.user).weekly_activity_target, 3)
