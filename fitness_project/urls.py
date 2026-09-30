from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import RedirectView
from accounts import views as accounts
from accounts import management_views
from health import views as health
from dashboard.views import dashboard
from dashboard.reports import reports
from health import features

urlpatterns = [
    path('foods/', features.foods, name='foods'),
    path('foods/<int:pk>/delete/', features.delete_food, name='food_delete'),
    path('meals/calculate/', features.calculated_meal, name='calculated_meal'),
    path('reminders/', features.reminders, name='reminders'),
    path('reminders/snooze/', features.snooze, name='reminder_snooze'),
    path('goals/personal/', features.personal_goals, name='personal_goals'),
    path('goals/personal/add/', features.edit_goal, name='personal_goal_add'),
    path('goals/personal/<int:pk>/edit/', features.edit_goal, name='personal_goal_edit'),
    path('goals/personal/<int:pk>/delete/', features.delete_goal, name='personal_goal_delete'),
    path('reports/', reports, name='reports'),
    path('reports/pdf/', reports, {'pdf': True}, name='report_pdf'),
path('accounts/manage/', management_views.account_list, name='manage_accounts'), path('accounts/manage/<int:pk>/access/', management_views.change_access, name='change_account_access'), path('', RedirectView.as_view(pattern_name='dashboard', permanent=False)), path('admin/', admin.site.urls), path('register/', accounts.register, name='register'), path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'), path('logout/', auth_views.LogoutView.as_view(), name='logout'), path('profile/', accounts.profile, name='profile'), path('dashboard/', dashboard, name='dashboard'), path('goals/', health.goals, name='goals')]
for kind in health.KINDS:
    urlpatterns += [path(f'{kind}/', health.records, {'kind': kind}, name=kind), path(f'{kind}/add/', health.edit_record, {'kind': kind}, name=f'{kind}_add'), path(f'{kind}/<int:pk>/edit/', health.edit_record, {'kind': kind}, name=f'{kind}_edit'), path(f'{kind}/<int:pk>/delete/', health.delete_record, {'kind': kind}, name=f'{kind}_delete')]
admin.site.site_header = 'Administration · Forma'
admin.site.site_title = 'Forma'
