# Generated by Django 5.0.9 on 2024-09-23 05:55

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_workout_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workout',
            name='date',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='workout',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=core.models.workout_image_file_path),
        ),
    ]
