# coding: utf-8

from django.core.management.base import BaseCommand
from django.db.models import Sum, Count
from plp.models import Course, CourseSession
from plp_extension.apps.course_review.models import CourseStudentRating


class Command(BaseCommand):
    help = u'Переоценка всех курсов по их CourseStudentRating'

    def handle(self, *args, **options):
        for c in Course.objects.values_list('id', flat=True):
            data = CourseStudentRating.objects.filter(
                session__rating_enabled=True,
                session__course__id=c,
                declined=False,
                status='published').aggregate(sr=Sum('rating'), cnt=Count('rating'))
            if data['sr'] is None:
                data['sr'] = 0
            Course.objects.filter(id=c).update(sum_ratings=data['sr'], count_ratings=data['cnt'])

        for cs in CourseSession.objects.values_list('id', flat=True):
            data = CourseStudentRating.objects.filter(
                session__rating_enabled=True,
                session__id=cs,
                declined=False,
                status='published').aggregate(sr=Sum('rating'), cnt=Count('rating'))
            if data['sr'] is None:
                data['sr'] = 0
            CourseSession.objects.filter(id=cs).update(sum_ratings=data['sr'], count_ratings=data['cnt'])
