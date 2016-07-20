# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('course_review', '0007_coursestudentratingquestions'),
    ]

    operations = [
        migrations.AddField(
            model_name='coursestudentfeedback',
            name='anon',
            field=models.BooleanField(default=False, verbose_name='\u0410\u043d\u043e\u043d\u0438\u043c\u043d\u043e'),
        ),
    ]
