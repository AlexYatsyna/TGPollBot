# Generated by Django 3.2.9 on 2021-12-05 08:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webBot', '0011_textquestion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='textquestion',
            name='user_answer',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]