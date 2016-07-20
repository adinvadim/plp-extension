# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('course_review', '0003_coursestudentratingclaim'),
    ]

    operations = [
        migrations.AddField(
            model_name='coursestudentrating',
            name='declined',
            field=models.BooleanField(default=False, verbose_name='\u041e\u0442\u0437\u044b\u0432 \u043e\u0442\u043a\u043b\u043e\u043d\u0435\u043d'),
        ),
    ]
