# Generated by Django 3.2.9 on 2021-12-05 00:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webBot', '0009_simplepoll_question_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='simplepoll',
            name='question_number',
            field=models.IntegerField(),
        ),
    ]