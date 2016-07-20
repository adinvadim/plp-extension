# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('course_review', '0006_disable_ratings_and_feedbacks_addition'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseStudentRatingQuestions',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.TextField(verbose_name='\u0422\u0435\u043a\u0441\u0442 \u0432\u043e\u043f\u0440\u043e\u0441\u0430')),
                ('csrating', models.ForeignKey(verbose_name='\u041e\u0442\u0437\u044b\u0432', to='course_review.CourseStudentRating')),
                ('teacher', models.ForeignKey(verbose_name='\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c, \u043e\u0442\u043f\u0440\u0430\u0432\u0438\u0432\u0448\u0438\u0439 \u0432\u043e\u043f\u0440\u043e\u0441', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '\u0412\u043e\u043f\u0440\u043e\u0441 \u043f\u043e \u043e\u0442\u0437\u044b\u0432\u0443',
                'verbose_name_plural': '\u0412\u043e\u043f\u0440\u043e\u0441\u044b \u043f\u043e \u043e\u0442\u0437\u044b\u0432\u0430\u043c',
            },
        ),
        migrations.AlterUniqueTogether(
            name='coursestudentratingquestions',
            unique_together=set([('teacher', 'csrating')]),
        ),
    ]
