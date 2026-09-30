from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import Food, Meal, MealItem, PersonalGoal, WeightReminder, WeightRecord, Activity
from .features import reminder_status, goal_progress
from dashboard.reports import weekly_report

class FeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('features')
        self.other = User.objects.create_user('private')
        self.client.force_login(self.user)
        self.today = timezone.localdate()
        self.food = Food.objects.create(user=self.user, name='Produit test', kcal_per_100g=Decimal('123.45'))

    def payload(self):
        return {'name': 'Repas calculé', 'description': '', 'date': self.today.isoformat(), 'form-TOTAL_FORMS': '2', 'form-INITIAL_FORMS': '0', 'form-0-food': self.food.pk, 'form-0-grams': '150', 'form-1-food': self.food.pk, 'form-1-grams': '50'}

    def test_meal_total_snapshot_and_manual_edit(self):
        response = self.client.post(reverse('calculated_meal'), self.payload())
        self.assertRedirects(response, reverse('meals'))
        meal = Meal.objects.get(user=self.user)
        self.assertEqual(meal.calories, 247)
        self.assertEqual(meal.items.count(), 2)
        self.food.kcal_per_100g = 999
        self.food.save()
        self.food.delete()
        self.assertEqual(meal.items.first().kcal_per_100g, Decimal('123.45'))
        self.assertContains(self.client.get(reverse('meals')), 'Produit test')
        self.client.post(reverse('meals_edit', args=[meal.pk]), {'name': meal.name, 'description': '', 'date': self.today.isoformat(), 'calories': 100})
        meal.refresh_from_db()
        self.assertEqual(meal.calories, 100)
        self.assertFalse(meal.items.exists())

    def test_food_id_tampering_and_invalid_quantity(self):
        foreign = Food.objects.create(user=self.other, name='Secret', kcal_per_100g=100)
        for change in [{'form-0-food': foreign.pk}, {'form-0-grams': '-1'}, {'form-0-grams': 'nan'}, {'form-TOTAL_FORMS': '1000'}]:
            response = self.client.post(reverse('calculated_meal'), {**self.payload(), **change})
            self.assertEqual(response.status_code, 200)
            self.assertFalse(Meal.objects.exists())
        self.assertEqual(self.client.post(reverse('food_delete', args=[foreign.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse('foods')), 'Secret')

    def test_calorie_limit_is_atomic(self):
        self.food.kcal_per_100g = 1000
        self.food.save()
        response = self.client.post(reverse('calculated_meal'), {**self.payload(), 'form-0-grams': '10000'})
        self.assertContains(response, '20 000')
        self.assertFalse(Meal.objects.exists())
        self.assertFalse(MealItem.objects.exists())

    def test_reminder_interval_snooze_disable(self):
        self.assertIsNotNone(reminder_status(self.user))
        self.client.post(reverse('reminder_snooze'))
        self.assertIsNone(reminder_status(self.user))
        with patch('health.features.timezone.localdate', return_value=self.today+timedelta(days=1)):
            self.assertIsNotNone(reminder_status(self.user))
        reminder = WeightReminder.objects.get(user=self.user)
        reminder.snoozed_until = None
        reminder.save()
        record = WeightRecord.objects.create(user=self.user, weight=75, date=self.today-timedelta(days=6))
        self.assertIsNone(reminder_status(self.user))
        record.date -= timedelta(days=1)
        record.save()
        self.assertIsNotNone(reminder_status(self.user))
        self.client.post(reverse('reminders'), {'interval_days': 7})
        self.assertIsNone(reminder_status(self.user))

    def test_custom_goal_progress_dates_and_privacy(self):
        goal = PersonalGoal.objects.create(user=self.user, title='Bouger', metric='minutes', target=60, start=self.today-timedelta(days=7), end=self.today)
        Activity.objects.create(user=self.user, name='Marche', duration=30, calories_burned=100, date=self.today)
        Activity.objects.create(user=self.other, name='Privé', duration=90, calories_burned=100, date=self.today)
        Activity.objects.create(user=self.user, name='Ancien', duration=90, calories_burned=100, date=self.today-timedelta(days=8))
        self.assertEqual(goal_progress(goal)['percent'], 50)
        goal.metric = 'sessions'
        self.assertEqual(goal_progress(goal)['actual'], 1)
        goal.metric = 'burned'
        self.assertEqual(goal_progress(goal)['actual'], 100)
        goal.metric = 'weighings'
        self.assertEqual(goal_progress(goal)['actual'], 0)
        foreign = PersonalGoal.objects.create(user=self.other, title='Secret', metric='minutes', target=60, start=self.today, end=self.today)
        self.assertEqual(self.client.get(reverse('personal_goal_edit', args=[foreign.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('personal_goal_delete', args=[foreign.pk])).status_code, 404)
        response = self.client.post(reverse('personal_goal_add'), {'title': 'Bad', 'metric': 'minutes', 'target': 0, 'start': self.today, 'end': self.today-timedelta(days=1)})
        self.assertTrue(response.context['form'].errors)

    def test_weekly_report_pdf_and_date_validation(self):
        monday = self.today-timedelta(days=self.today.weekday()+7)
        Meal.objects.create(user=self.user, name='Repas', calories=600, date=monday)
        Meal.objects.create(user=self.other, name='Secret', calories=9000, date=monday)
        Meal.objects.create(user=self.user, name='Autre semaine', calories=300, date=monday-timedelta(days=1))
        for days, weight in [(0, 80), (6, 79)]:
            WeightRecord.objects.create(user=self.user, weight=weight, date=monday+timedelta(days=days))
        data = weekly_report(self.user, monday+timedelta(days=2))
        self.assertEqual(data['consumed'], 600)
        self.assertEqual(data['weight_change'], -1)
        self.assertIsNone(data['rows'][1]['consumed'])
        self.assertEqual(data['meal_days'], 1)
        response = self.client.get(reverse('report_pdf'), {'week': monday.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF-'))
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertIn('no-store', response['Cache-Control'])
        for date in ['nonsense', '9999-12-31', '0001-01-01']:
            self.assertEqual(self.client.get(reverse('report_pdf'), {'week': date}).status_code, 400)

    def test_pages_and_anonymous_access(self):
        for name in ['foods', 'calculated_meal', 'reminders', 'personal_goals', 'personal_goal_add', 'reports', 'report_pdf']:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.client.logout()
        for name in ['foods', 'calculated_meal', 'reminders', 'personal_goals', 'reports', 'report_pdf']:
            self.assertEqual(self.client.get(reverse(name)).status_code, 302)
