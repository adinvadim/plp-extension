# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('plp', '0065_merge'),
        ('course_review', '0001_coursestudentfeedback'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseStudentRating',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rating', models.PositiveSmallIntegerField(verbose_name='\u041e\u0446\u0435\u043d\u043a\u0430', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('comment', models.TextField(default=b'', verbose_name='\u041f\u043e\u044f\u0441\u043d\u0435\u043d\u0438\u0435', blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('session', models.ForeignKey(verbose_name='\u0421\u0435\u0441\u0441\u0438\u044f \u043a\u0443\u0440\u0441\u0430', to='plp.CourseSession')),
                ('user', models.ForeignKey(verbose_name='\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='coursestudentrating',
            unique_together=set([('user', 'session')]),
        ),
    ]
