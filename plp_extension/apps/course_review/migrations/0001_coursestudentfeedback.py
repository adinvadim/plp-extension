# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('plp', '0065_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseStudentFeedback',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('feedback', models.TextField(verbose_name='\u041e\u0442\u0437\u044b\u0432', validators=[django.core.validators.MinLengthValidator(200, '\u041c\u0438\u043d\u0438\u043c\u0430\u043b\u044c\u043d\u0430\u044f \u0434\u043b\u0438\u043d\u0430 200 \u0441\u0438\u043c\u0432\u043e\u043b\u043e\u0432'), django.core.validators.MaxLengthValidator(10000, '\u041c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u0430\u044f \u0434\u043b\u0438\u043d\u0430 10000 \u0441\u0438\u043c\u0432\u043e\u043b\u043e\u0432')])),
                ('grade', models.PositiveSmallIntegerField(verbose_name='\u041e\u0446\u0435\u043d\u043a\u0430')),
                ('got_certificate', models.BooleanField(verbose_name='\u041f\u043e\u043b\u0443\u0447\u0435\u043d \u0441\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442')),
                ('status', models.CharField(default=b'review', max_length=15, verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441', choices=[(b'published', '\u041e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u043d'), (b'review', '\u041d\u0430 \u0440\u0435\u0432\u044c\u044e'), (b'rejected', '\u041e\u0442\u043a\u043b\u043e\u043d\u0435\u043d')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('session', models.ForeignKey(verbose_name='\u0421\u0435\u0441\u0441\u0438\u044f \u043a\u0443\u0440\u0441\u0430', to='plp.CourseSession')),
                ('user', models.ForeignKey(verbose_name='\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '\u041e\u0442\u0437\u044b\u0432 \u043e \u043a\u0443\u0440\u0441\u0435',
                'verbose_name_plural': '\u041e\u0442\u0437\u044b\u0432\u044b \u043e \u043a\u0443\u0440\u0441\u0435',
            },
        ),
        migrations.AlterUniqueTogether(
            name='coursestudentfeedback',
            unique_together=set([('user', 'session')]),
        ),
    ]
