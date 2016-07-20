# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('course_review', '0005_coursestudentrating_anon'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseFeedbackSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('disable_ratings', models.BooleanField(default=False, verbose_name='\u041e\u0442\u043a\u043b\u044e\u0447\u0438\u0442\u044c \u0432\u0440\u0435\u043c\u0435\u043d\u043d\u043e \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u043d\u043e\u0432\u044b\u0445 \u043e\u0442\u0437\u044b\u0432\u043e\u0432')),
                ('disable_feedbacks', models.BooleanField(default=False, verbose_name='\u041e\u0442\u043a\u043b\u044e\u0447\u0438\u0442\u044c \u0432\u0440\u0435\u043c\u0435\u043d\u043d\u043e \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u043d\u043e\u0432\u044b\u0445 \u0438\u0441\u0442\u043e\u0440\u0438\u0439')),
            ],
            options={
                'verbose_name': '\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438 \u043e\u0442\u0437\u044b\u0432\u043e\u0432',
                'verbose_name_plural': '\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438 \u043e\u0442\u0437\u044b\u0432\u043e\u0432',
            },
        ),
        migrations.AddField(
            model_name='coursestudentrating',
            name='status',
            field=models.CharField(default=b'published', max_length=15, verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441', choices=[(b'published', '\u041e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u043d\u043e'), (b'waiting', '\u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435')]),
        ),
        migrations.AlterField(
            model_name='coursestudentfeedback',
            name='status',
            field=models.CharField(default=b'review', max_length=15, verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441', choices=[(b'published', '\u041e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u043d'), (b'review', '\u041d\u0430 \u0440\u0435\u0432\u044c\u044e'), (b'rejected', '\u041e\u0442\u043a\u043b\u043e\u043d\u0435\u043d'), (b'waiting', '\u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435')]),
        ),
    ]
