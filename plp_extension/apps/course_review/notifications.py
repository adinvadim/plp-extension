# coding: utf-8

from django.core.urlresolvers import reverse
from django.conf import settings
from django.template.loader import get_template
from emails.django import Message
from plp.notifications.base import MassSendEmails
from plp.roles import RoleBase


class FeedbackEmailBase(MassSendEmails):
    """
    Базовый класс для сообщений, связанных с learner story, отправляется авторам курса
    """
    def __init__(self, feedback):
        self.session = feedback.session
        self.feedback = feedback
        super(FeedbackEmailBase, self).__init__()

    def get_emails(self):
        session = self.session
        course_key = '%s+%s+%s' % (session.course.university.slug, session.course.slug, session.slug)
        role = RoleBase('staff', course_key=course_key)
        self.user_by_email = dict([(user.email, user) for user in role.users_with_role()])
        return self.user_by_email.keys()

    def get_context(self, email=None):
        return {
            'session': self.session,
            'feedback': self.feedback,
            'user': self.user_by_email[email]
        }


class FeedbackPublishedEmail(FeedbackEmailBase):
    """
    Сообщение о публикации новой learner story
    """
    template_html = 'emails/course_feedback_published_html.html'
    template_subject = 'emails/course_feedback_published_subject.txt'


class FeedbackCreatedEmail(FeedbackEmailBase):
    """
    Сообщение о добавлении новой learner story
    """
    template_html = 'emails/course_feedback_created_html.html'
    template_subject = 'emails/course_feedback_created_subject.txt'

    def get_context(self, email=None):
        context = super(FeedbackCreatedEmail, self).get_context(email)
        context['link'] = reverse('feedback-moderation') + '?feedback={}'.format(self.feedback.id)
        context['site'] = self.get_site()
        return context


class RatingClaimReviewedEmail(MassSendEmails):
    """
    Сообщение о финальном статусе рассмотрения жалобы на курс, отправляется всем пользователям,
    оставлявшим жалобу
    """
    template_subject = 'emails/rating_claim_reviewed_subject.txt'
    template_html = 'emails/rating_claim_reviewed_message.html'
    extra_headers = {'Reply-To': settings.EMAIL_COURSE_RATING}

    def __init__(self, rating_claim):
        self.rating_claim = rating_claim
        self.session = rating_claim.csrating.session
        super(RatingClaimReviewedEmail, self).__init__()

    def get_emails(self):
        return self.rating_claim._meta.model.objects.filter(
            csrating=self.rating_claim.csrating
        ).values_list('teacher__email', flat=True)

    def get_context(self, email=None):
        return {
            'rating': self.rating_claim.csrating,
            'status': self.rating_claim.resolution
        }


def send_question_to_user(csrq):
    """
    Отправка вопроса от автора курса автору неанонимного отзыва с обратным адресом преподавателя
    """
    context = {
        'teacher': csrq.teacher,
        'user': csrq.csrating.user,
        'session': csrq.csrating.session,
        'question': csrq.text,
        'rating': csrq.csrating,
    }
    to_name = u'%s %s' % (context['user'].last_name, context['user'].first_name)
    to_email = context['user'].email
    m = Message(
        subject=get_template('emails/rating_question_subject.txt'),
        html=get_template('emails/rating_question_message.html'),
        mail_from=settings.EMAIL_NOTIFICATIONS_FROM,
        mail_to=(to_name, to_email),
        headers={'Reply-To': context['teacher'].email},
    )
    m.send(context={'context': context})
