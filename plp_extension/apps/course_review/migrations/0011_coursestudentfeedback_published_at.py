# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('course_review', '0010_auto_20160714_1914'),
    ]

    operations = [
        migrations.AddField(
            model_name='coursestudentfeedback',
            name='published_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
