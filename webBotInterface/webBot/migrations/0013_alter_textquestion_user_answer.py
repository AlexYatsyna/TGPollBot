# Generated by Django 3.2.9 on 2021-12-05 08:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webBot', '0012_alter_textquestion_user_answer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='textquestion',
            name='user_answer',
            field=models.CharField(blank=True, default=' ', max_length=255),
        ),
    ]