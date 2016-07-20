# coding: utf-8

from django import template
from plp_extension.apps.course_review.models import CourseStudentRating, CourseStudentFeedback

register = template.Library()


@register.assignment_tag(takes_context=True)
def user_left_rating(context, session):
    """
    возвращает объект CourseStudentRating или None для пользователя и сессии курса
    """
    user = context['request'].user
    if user and user.is_authenticated():
        try:
            return CourseStudentRating.objects.get(session=session, user=user, status='published', declined=False)
        except CourseStudentRating.DoesNotExist:
            return None
    return None


@register.assignment_tag(takes_context=True)
def user_left_story(context, session):
    """
    возвращает объект CourseStudentFeedback или None для пользователя и сессии курса
    """
    user = context['request'].user
    if user and user.is_authenticated():
        try:
            return CourseStudentFeedback.objects.get(session=session, user=user, status='published')
        except CourseStudentFeedback.DoesNotExist:
            return None
    return None


@register.assignment_tag(takes_context=True)
def count_stories_for_sessions(context, sessions, left=True):
    """
    :param context:
    :param sessions: iterable сессии
    :param left:
    :return: количество сессий, по которым оставлены или не оставлены истории для left = False, True соответственно
    """
    user = context['request'].user
    session_ids = [i.id for i in sessions]
    sessions_cnt = len(sessions)
    stories_left = 0
    if user and user.is_authenticated():
        stories_left = CourseStudentFeedback.objects.filter(session__id__in=session_ids, user=user).count()
    if left:
        return sessions_cnt - stories_left
    return stories_left
