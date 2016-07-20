# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('course_review', '0008_coursestudentfeedback_anon'),
    ]

    operations = [
        migrations.AddField(
            model_name='coursestudentfeedback',
            name='cons',
            field=models.TextField(default=b'', blank=True, verbose_name='\u041d\u0435\u0434\u043e\u0441\u0442\u0430\u0442\u043a\u0438', validators=[django.core.validators.MaxLengthValidator(10000, '\u041c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u0430\u044f \u0434\u043b\u0438\u043d\u0430 10000 \u0441\u0438\u043c\u0432\u043e\u043b\u043e\u0432')]),
        ),
        migrations.AddField(
            model_name='coursestudentfeedback',
            name='pros',
            field=models.TextField(default=b'', blank=True, verbose_name='\u0414\u043e\u0441\u0442\u043e\u0438\u043d\u0441\u0442\u0432\u0430', validators=[django.core.validators.MaxLengthValidator(10000, '\u041c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u0430\u044f \u0434\u043b\u0438\u043d\u0430 10000 \u0441\u0438\u043c\u0432\u043e\u043b\u043e\u0432')]),
        ),
    ]
