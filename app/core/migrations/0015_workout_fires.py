# Generated by Django 5.0.9 on 2024-10-10 13:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='workout',
            name='fires',
            field=models.IntegerField(default=0),
        ),
    ]
