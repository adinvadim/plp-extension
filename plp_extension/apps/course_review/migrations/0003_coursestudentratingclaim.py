# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('course_review', '0002_coursestudentrating'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseStudentRatingClaim',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('reason', models.TextField(verbose_name='\u041f\u0440\u0438\u0447\u0438\u043d\u0430 \u0443\u0434\u0430\u043b\u0435\u043d\u0438\u044f')),
                ('resolution', models.CharField(default=b'review', max_length=15, verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441', choices=[(b'review', '\u041d\u0430 \u0440\u0430\u0441\u0441\u043c\u043e\u0442\u0440\u0435\u043d\u0438\u0438'), (b'accepted', '\u041f\u0440\u0438\u043d\u044f\u0442\u043e'), (b'declined', '\u041e\u0442\u043a\u043b\u043e\u043d\u0435\u043d\u043e')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('csrating', models.ForeignKey(verbose_name='\u041e\u0442\u0437\u044b\u0432', to='course_review.CourseStudentRating')),
                ('teacher', models.ForeignKey(verbose_name='\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c, \u0437\u0430\u043f\u0440\u043e\u0441\u0438\u0432\u0448\u0438\u0439 \u0443\u0434\u0430\u043b\u0435\u043d\u0438\u0435', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '\u0416\u0430\u043b\u043e\u0431\u0430 \u043d\u0430 \u043e\u0442\u0437\u044b\u0432 \u043e \u043a\u0443\u0440\u0441\u0435',
                'verbose_name_plural': '\u0416\u0430\u043b\u043e\u0431\u044b \u043d\u0430 \u043e\u0442\u0437\u044b\u0432 \u043e \u043a\u0443\u0440\u0441\u0435',
            },
        ),
        migrations.AlterUniqueTogether(
            name='coursestudentratingclaim',
            unique_together=set([('teacher', 'csrating')]),
        ),
    ]
