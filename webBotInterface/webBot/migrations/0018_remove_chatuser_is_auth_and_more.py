# Generated by Django 4.0 on 2021-12-12 15:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webBot', '0017_chatuser_is_auth_chatuser_is_group_selected_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='chatuser',
            name='is_auth',
        ),
        migrations.RemoveField(
            model_name='chatuser',
            name='is_group_selected',
        ),
        migrations.RemoveField(
            model_name='chatuser',
            name='is_start',
        ),
        migrations.AddField(
            model_name='chatuser',
            name='registration_state',
            field=models.IntegerField(default=0),
        ),
    ]