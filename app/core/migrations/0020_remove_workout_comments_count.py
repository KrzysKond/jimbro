# Generated by Django 5.0.9 on 2024-10-13 22:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_workout_comments_count'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workout',
            name='comments_count',
        ),
    ]
