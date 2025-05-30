# Generated by Django 5.1.7 on 2025-04-08 15:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Audience',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Название аудитории')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Описание аудитории')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
            ],
            options={
                'verbose_name': 'Аудитория',
                'verbose_name_plural': 'Аудитории',
            },
        ),
        migrations.CreateModel(
            name='AudienceImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='audience_images/', verbose_name='Изображение')),
                ('description', models.CharField(blank=True, max_length=255, null=True, verbose_name='Описание изображения')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('audience', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='virtmuseum.audience', verbose_name='Аудитория')),
            ],
            options={
                'verbose_name': 'Изображение аудитории',
                'verbose_name_plural': 'Изображения аудиторий',
            },
        ),
        migrations.CreateModel(
            name='Characteristic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Название характеристики')),
                ('value', models.CharField(max_length=255, verbose_name='Значение характеристики')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('audience', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='characteristics', to='virtmuseum.audience', verbose_name='Аудитория')),
            ],
            options={
                'verbose_name': 'Характеристика',
                'verbose_name_plural': 'Характеристики',
            },
        ),
    ]
