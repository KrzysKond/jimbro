# Generated by Django 5.0.9 on 2024-10-13 22:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='workout',
            name='comments_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
