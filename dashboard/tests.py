from datetime import date, timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from health.models import Activity, Goal, Meal, WeightRecord
from .analytics import analyze


class AnalyticsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('reader')
        self.other = User.objects.create_user('other')
        self.today = date(2026, 9, 25)

    def weight(self, days, value, user=None):
        return WeightRecord.objects.create(user=user or self.user, date=self.today - timedelta(days=days), weight=value)

    def test_insufficient_and_out_of_window_data(self):
        self.weight(40, 80)
        self.weight(2, 79)
        self.weight(1, 78)
        self.weight(0, 77)
        self.assertIsNone(analyze(self.user, self.today)['weight'])

    def test_regression_uses_actual_elapsed_days(self):
        for days, weight in [(14, 80), (10, 79.6), (0, 78.6)]:
            self.weight(days, weight)
        self.weight(1, 300, self.other)
        Goal.objects.create(user=self.user, target_weight=75)
        result = analyze(self.user, self.today)
        self.assertEqual(result['weight']['weekly_slope'], -0.7)
        self.assertEqual(result['weight']['r_squared'], 1)
        self.assertEqual(result['weight']['count'], 3)
        self.assertTrue(any('se rapproche' in item for item in result['messages']))

    def test_flat_trend_and_stale_data(self):
        for days in [27, 20, 10]:
            self.weight(days, 80)
        data = analyze(self.user, self.today)['weight']
        self.assertEqual(data['weekly_slope'], 0)
        self.assertIsNone(data['r_squared'])
        self.assertTrue(data['stale'])

    def test_target_crossing_does_not_claim_progress(self):
        for days, weight in [(14, 80), (7, 78), (0, 76)]:
            self.weight(days, weight)
        Goal.objects.create(user=self.user, target_weight=79)
        messages = analyze(self.user, self.today)['messages']
        self.assertFalse(any('se rapproche' in item for item in messages))
        self.assertTrue(any('s’éloigne' in item for item in messages))

    def test_meals_only_average_logged_completed_days(self):
        Goal.objects.create(user=self.user, daily_calorie_target=1500)
        for days, calories in [(1, 1000), (1, 1000), (3, 1000), (0, 9000), (15, 9000)]:
            Meal.objects.create(user=self.user, name='Repas', calories=calories, date=self.today-timedelta(days=days))
        Meal.objects.create(user=self.other, name='Privé', calories=9000, date=self.today-timedelta(days=1))
        data = analyze(self.user, self.today)['nutrition']
        self.assertEqual(data['average'], 1500)
        self.assertEqual(data['days'], 2)
        self.assertEqual(data['over_target'], 1)

    def test_activity_compares_completed_calendar_weeks(self):
        for day in [date(2026, 9, 7), date(2026, 9, 14), date(2026, 9, 20), date(2026, 9, 21)]:
            Activity.objects.create(user=self.user, name='Marche', duration=30, calories_burned=100, date=day)
        Activity.objects.create(user=self.other, name='Privé', duration=60, calories_burned=500, date=date(2026, 9, 20))
        data = analyze(self.user, self.today)['activity']
        self.assertEqual((data['previous'], data['latest'], data['delta'], data['minutes']), (1, 2, 1, 60))

    def test_empty_data(self):
        result = analyze(self.user, self.today)
        for key in ['weight', 'nutrition', 'activity']:
            self.assertIsNone(result[key])
        self.assertTrue(result['messages'])
