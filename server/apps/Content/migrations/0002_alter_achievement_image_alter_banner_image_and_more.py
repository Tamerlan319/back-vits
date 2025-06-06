# Generated by Django 5.1.7 on 2025-05-28 02:46

import server.settings.environments.storage_backends
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Content', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='achievement',
            name='image',
            field=models.ImageField(storage=server.settings.environments.storage_backends.YandexMediaStorage(), upload_to='achievements/'),
        ),
        migrations.AlterField(
            model_name='banner',
            name='image',
            field=models.ImageField(storage=server.settings.environments.storage_backends.YandexMediaStorage(), upload_to='banners/'),
        ),
        migrations.AlterField(
            model_name='review',
            name='image',
            field=models.ImageField(blank=True, null=True, storage=server.settings.environments.storage_backends.YandexMediaStorage(), upload_to='reviews/'),
        ),
    ]
