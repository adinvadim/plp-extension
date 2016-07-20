# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('course_review', '0009_coursestudentfeedback_pros_cons'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='coursestudentfeedback',
            name='cons',
        ),
        migrations.RemoveField(
            model_name='coursestudentfeedback',
            name='feedback',
        ),
        migrations.RemoveField(
            model_name='coursestudentfeedback',
            name='pros',
        ),
        migrations.AddField(
            model_name='coursestudentfeedback',
            name='data',
            field=jsonfield.fields.JSONField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='coursestudentfeedback',
            name='rating',
            field=models.IntegerField(default=None, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)]),
        ),
        migrations.AddField(
            model_name='coursestudentrating',
            name='cons',
            field=models.TextField(default=b'', null=True, verbose_name='\u041d\u0435\u0434\u043e\u0441\u0442\u0430\u0442\u043a\u0438', blank=True),
        ),
        migrations.AddField(
            model_name='coursestudentrating',
            name='pros',
            field=models.TextField(default=b'', null=True, verbose_name='\u0414\u043e\u0441\u0442\u043e\u0438\u043d\u0441\u0442\u0432\u0430', blank=True),
        ),
    ]
