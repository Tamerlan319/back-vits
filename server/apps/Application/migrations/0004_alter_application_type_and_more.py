# Generated by Django 5.1.7 on 2025-05-30 03:57

import server.settings.environments.storage_backends
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Application', '0003_alter_application_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='type',
            field=models.CharField(choices=[('academic', 'Академический отпуск'), ('translation', 'Перевод на другой факультет'), ('reference', 'Справка об обучении'), ('retake', 'Пересдача экзамента')], max_length=50, verbose_name='Тип заявления'),
        ),
        migrations.AlterField(
            model_name='applicationattachment',
            name='file',
            field=models.FileField(storage=server.settings.environments.storage_backends.PrivateMediaStorage(), upload_to='applications/attachments/', verbose_name='Файл'),
        ),
    ]
