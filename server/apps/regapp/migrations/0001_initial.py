# Generated by Django 3.2.25 on 2025-03-07 11:13

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(verbose_name='Наименование операции')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Описание операции')),
                ('cost', models.FloatField(verbose_name='Стоимость')),
                ('operation_at', models.DateTimeField(default=datetime.datetime.now, verbose_name='Дата операции')),
            ],
            options={
                'verbose_name': 'Операция',
                'verbose_name_plural': 'Операции',
            },
        ),
    ]
