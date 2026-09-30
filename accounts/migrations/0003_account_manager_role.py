from django.db import migrations


def create_role(apps, schema_editor):
    alias = schema_editor.connection.alias
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    Group = apps.get_model('auth', 'Group')
    ct, _ = ContentType.objects.using(alias).get_or_create(app_label='accounts', model='profile')
    permission, _ = Permission.objects.using(alias).get_or_create(content_type=ct, codename='manage_accounts', defaults={'name': 'Peut activer ou désactiver les comptes ordinaires'})
    group, _ = Group.objects.using(alias).get_or_create(name='Responsables des comptes')
    group.permissions.add(permission)


class Migration(migrations.Migration):
    dependencies = [('accounts', '0002_alter_profile_options'), ('auth', '0012_alter_user_first_name_max_length')]
    operations = [migrations.RunPython(create_role, migrations.RunPython.noop)]
