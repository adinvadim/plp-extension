# -*- coding: utf-8 -*-

from django.conf.urls import url, patterns
from plp_extension.apps.course_review.views import FeedbackModerationView, CourseRatingView, RatingClaimModerationView, \
    CourseRatingByDateView, TeacherCoursesRatingByDateView

urlpatterns = patterns('plp_extension.apps.course_review.views',
    url(r'^feedback-moderation/?$', FeedbackModerationView.as_view(), name='feedback-moderation'),
    url(r'^rate-course/(?P<course_session_id>\d+)/?$', 'rate_course', name='rate-course'),
    url(r'^leave-course-feedback/(?P<course_session_id>\d+)/?$', 'leave_course_feedback', name='leave-course-feedback'),
    url(r'^course-rating/(?P<uni_slug>[-\w]+)/(?P<course_slug>[-\w]+)/(?P<session_slug>[-\w]+)/?$',
        CourseRatingView.as_view(), name='course-rating'),
    url(r'^rating-claim-moderation/?$', RatingClaimModerationView.as_view(), name='rating-claim-moderation'),
    url(r'^course-rating-question/?$', 'handle_rating_question', name='course-rating-question'),
    url(r'^course-rating-claim/?$', 'handle_rating_claim', name='handle-rating-claim'),
    url(r'^course/(?P<uni_slug>[-\w]+)/(?P<course_slug>[-\w]+)/course_rating/(?P<date>\d{4}_\d{2}_\d{2})/?$',
        CourseRatingByDateView.as_view(), name='course-rating-by-date'),
    url(r'^courses/(?P<username>[-\w_.]+)/(?P<date>\d{4}_\d{2}_\d{2})/?$',
        TeacherCoursesRatingByDateView.as_view(), name='teacher-course-rating-by-date'),
    url(r'^course-rating-and-feedback-list/(?P<course_id>\d+)/?$', 'course_rating_and_feedback_list',
        name='course-rating-and-feedback-list'),
    url(r'^course/(?P<uni_slug>[-\w]+)/(?P<slug>[-\w]+)/review/?$', 'course_rating_page', name='course-reviews'),
    url(r'^leave-course-response/(?P<uni_slug>[-\w]+)/(?P<course_slug>[-\w]+)/(?P<session_slug>[-\w]+)/?$',
        'leave_course_rating_view', name='leave-course-response'),
    url(r'^leave-course-response/(?P<uni_slug>[-\w]+)/(?P<course_slug>[-\w]+)/(?P<session_slug>[-\w]+)/thanks-for-review/?$',
        'thanks_for_review', name='thanks-for-review'),
)
