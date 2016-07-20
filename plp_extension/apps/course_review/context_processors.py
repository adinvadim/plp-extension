# coding: utf-8

from django.conf import settings


def course_review_settings(request):
    return {
        'ENABLE_COURSE_RATING': getattr(settings, 'ENABLE_COURSE_RATING', False),
    }
