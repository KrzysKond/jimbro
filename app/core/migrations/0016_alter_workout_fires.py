# Generated by Django 5.0.9 on 2024-10-10 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_workout_fires'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workout',
            name='fires',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
