# Generated by Django 5.0.9 on 2024-10-15 16:29

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_workout_comments_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='profile_picture',
            field=models.ImageField(null=True, upload_to=core.models.user_image_file_path),
        ),
    ]