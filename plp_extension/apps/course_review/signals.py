# coding: utf-8

from django.dispatch import Signal
from django.db.models import F
from plp_extension.apps.course_review.notifications import FeedbackPublishedEmail, FeedbackCreatedEmail, RatingClaimReviewedEmail
from plp.models import Course, CourseSession

course_feedback_created = Signal(providing_args=['instance'])
course_feedback_published = Signal(providing_args=['instance'])
rating_claim_reviewed = Signal(providing_args=['instance'])
course_rating_updated_or_created = Signal(providing_args=['instance', 'updated', 'old_value', 'value'])


def send_course_feedback_published_email(**kwargs):
    instance = kwargs.get('instance')
    if instance:
        emails = FeedbackPublishedEmail(instance)
        emails.send()


def send_course_feedback_created_email(**kwargs):
    instance = kwargs.get('instance')
    if instance:
        emails = FeedbackCreatedEmail(instance)
        emails.send()


def update_mean_ratings(**kwargs):
    instance = kwargs.get('instance')
    old_value = float(kwargs.get('old_value'))
    value = float(kwargs.get('value'))
    updated = kwargs.get('updated')
    deleted = kwargs.get('deleted')
    delta = value - old_value
    upd_dict = {'sum_ratings': F('sum_ratings') + delta}
    if deleted:
        upd_dict['count_ratings'] = F('count_ratings') - 1
    elif not updated:
        upd_dict['count_ratings'] = F('count_ratings') + 1
    Course.objects.filter(id=instance.session.course.id).update(**upd_dict)
    CourseSession.objects.filter(id=instance.session.id).update(**upd_dict)


def handle_rating_claim_reviewed(**kwargs):
    instance = kwargs.get('instance')
    if instance:
        instance._meta.model.objects.filter(csrating=instance.csrating).update(resolution=instance.resolution)
        msgs = RatingClaimReviewedEmail(instance)
        msgs.send()
