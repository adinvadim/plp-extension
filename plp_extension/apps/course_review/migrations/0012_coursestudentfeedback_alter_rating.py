# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('course_review', '0011_coursestudentfeedback_published_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursestudentfeedback',
            name='rating',
            field=models.IntegerField(default=None, null=True, blank=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)]),
        ),
    ]
