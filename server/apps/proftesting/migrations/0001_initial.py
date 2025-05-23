# Generated by Django 5.1.7 on 2025-05-01 15:21

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('directions', '0002_remove_program_created'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AnswerOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(verbose_name='Текст вопроса')),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='AnswerProgramWeight',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight', models.IntegerField(default=1)),
                ('answer_option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='proftesting.answeroption')),
                ('program', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='directions.program')),
            ],
            options={
                'unique_together': {('answer_option', 'program')},
            },
        ),
        migrations.AddField(
            model_name='answeroption',
            name='program_weights',
            field=models.ManyToManyField(related_name='answer_options', through='proftesting.AnswerProgramWeight', to='directions.program'),
        ),
        migrations.AddField(
            model_name='answeroption',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='proftesting.question'),
        ),
        migrations.CreateModel(
            name='QuestionGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('education_level', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='directions.educationlevel')),
            ],
        ),
        migrations.AddField(
            model_name='question',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='questions', to='proftesting.questiongroup'),
        ),
        migrations.CreateModel(
            name='TestSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed', models.BooleanField(default=False)),
                ('education_level', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='directions.educationlevel')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TestResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('recommended_programs', models.ManyToManyField(to='directions.program')),
                ('session', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='result', to='proftesting.testsession')),
            ],
        ),
        migrations.CreateModel(
            name='UserAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='proftesting.answeroption')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='proftesting.question')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='proftesting.testsession')),
            ],
            options={
                'unique_together': {('session', 'question')},
            },
        ),
    ]
