# Generated by Django 5.1.7 on 2025-03-18 14:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0007_news_slug'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='news',
            name='slug',
        ),
    ]
