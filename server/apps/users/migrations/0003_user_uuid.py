# Generated by Django 5.1.7 on 2025-05-30 08:23

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_verification_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='uuid',
            field=models.UUIDField(blank=True, default=uuid.uuid4, editable=False, null=True),
        ),
    ]
