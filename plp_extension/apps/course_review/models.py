# coding: utf-8

import logging
from django.db import models
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from plp.models import Participant, Course
from plp_extension.apps.course_review.signals import *


class CourseStudentFeedback(models.Model):
    """
    Модель для user learner story - отзывы окончивших курс пользователей, статус модерируется автором курса,
    при добавлении новой learner story авторам курса отправляется сообщение
    """
    STATUSES = (
        ('published', _(u'Опубликован')),
        ('review', _(u'На ревью')),
        ('rejected', _(u'Отклонен')),
        ('waiting', _(u'Ожидание')),
    )
    # ожидаемые в data поля
    _data_fields = [
        'rating',
        'comment_why',
        'comment_new',
        'comment_apply',
        'comment_advise',
        'comment_suggest',
        'comment',
    ]
    user = models.ForeignKey('plp.User', verbose_name=_(u'Пользователь'))
    session = models.ForeignKey('plp.CourseSession', verbose_name=_(u'Сессия курса'))
    data = JSONField(blank=True, null=True)
    rating = models.IntegerField(default=None, null=True, blank=True, validators=[
        validators.MinValueValidator(0),
        validators.MaxValueValidator(10)
    ])
    grade = models.PositiveSmallIntegerField(verbose_name=_(u'Оценка'))
    got_certificate = models.BooleanField(verbose_name=_(u'Получен сертификат'))
    status = models.CharField(max_length=15, choices=STATUSES, verbose_name=_(u'Статус'), default='review')
    anon = models.BooleanField(verbose_name=_(u'Анонимно'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'session')
        verbose_name = _(u'Отзыв о курсе')
        verbose_name_plural = _(u'Отзывы о курсе')

    def __unicode__(self):
        return u'%s - %s' % (self.user, self.session)

    def clean_fields(self, exclude=None):
        data = self._clean_data()
        self.rating = data.get('rating')
        super(CourseStudentFeedback, self).clean_fields(exclude)
        user = getattr(self, 'user', None)
        session = getattr(self, 'session', None)
        if user and session:
            p = Participant.objects.filter(user=user, session=session)
            if not p:
                raise ValidationError(_(u'Пользователь не записан на этот курс'))
            p = p[0]
            if not (p.certificate_data and p.is_graduate):
                raise ValidationError(_(u'Обучение на курсе еще не завершено'))
        filled_fields = len([i for i in data.values() if unicode(i).strip()])
        if filled_fields < 2:
            raise ValidationError(_(u'Пожалуйста, ответьте по меньшей мере на два вопроса.'))

    def can_edit(self):
        """
        может ли пользователь редактировать историю
        """
        if self.status != 'published':
            check_time = True
        else:
            t = self.published_at or self.created_at
            check_time = timezone.now() - t < timezone.timedelta(hours=24)
        return check_time

    def _clean_data(self):
        data = getattr(self, 'data', {}) or {}
        data = dict([(k, v) for k, v in data.iteritems() if k in self._data_fields])
        return data

    def save(self, **kwargs):
        cert = Participant.objects.get(user=self.user, session=self.session).certificate_data
        self.grade = cert['grade']
        self.got_certificate = cert['passed']
        self.rating = self.data.get('rating')
        self.data = self._clean_data()
        new = not self.id
        super(CourseStudentFeedback, self).save(**kwargs)
        if new:
            course_feedback_created.send(CourseStudentFeedback, instance=self)
            msg = _(u'Пользователь %(user)s оставил расширенный отзыв %(f_id)s по курсу %(univ)s %(course)s %(session)s')
            logging.info(msg % {
                'user': self.user.username,
                'f_id': self.id,
                'univ': self.session.course.university.title,
                'course': self.session.course.title,
                'session': self.session.slug
            })


class CourseStudentRating(models.Model):
    """
    Модель для оценок и отзывов на курс от записанных на него пользователей
    """
    STATUS = (
        ('published', _(u'Опубликовано')),
        ('waiting', _(u'Ожидание')),
    )
    user = models.ForeignKey('plp.User', verbose_name=_(u'Пользователь'))
    session = models.ForeignKey('plp.CourseSession', verbose_name=_(u'Сессия курса'))
    rating = models.PositiveSmallIntegerField(verbose_name=_(u'Оценка'), validators=[
        validators.MinValueValidator(1),
        validators.MaxValueValidator(5)
    ])
    comment = models.TextField(verbose_name=_(u'Пояснение'), default='', blank=True)
    pros = models.TextField(verbose_name=_(u'Достоинства'), default='', blank=True, null=True)
    cons = models.TextField(verbose_name=_(u'Недостатки'), default='', blank=True, null=True)
    declined = models.BooleanField(verbose_name=_(u'Отзыв отклонен'), default=False)
    anon = models.BooleanField(verbose_name=_(u'Анонимно'), default=False)
    status = models.CharField(verbose_name=_(u'Статус'), max_length=15, choices=STATUS, default='published')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'session')

    def __unicode__(self):
        return u'%s - %s' % (self.user, self.session)

    def clean_fields(self, exclude=None):
        super(CourseStudentRating, self).clean_fields(exclude)
        user = getattr(self, 'user', None)
        session = getattr(self, 'session', None)
        if user and session:
            if not Participant.objects.filter(user=user, session=session).exists():
                raise ValidationError(_(u'Пользователь не записан на курс'))
        if not getattr(self, 'comment', '').strip():
            raise ValidationError(_(u'Заполните поле "пояснение"'))
        comment = getattr(self, 'comment', '')
        if comment and not (100 <= len(comment) <= 1000):
            raise ValidationError(_(u'Пояснение должно занимать от 100 до 1000 символов'))

    def can_edit(self):
        """
        может ли пользователь редактировать отзыв
        """
        check_status = not self.declined
        check_time = timezone.now() - self.created_at < timezone.timedelta(hours=24)
        return check_status and check_time


class CourseStudentRatingClaim(models.Model):
    """
    Жалобы на отзывы (CourseStudentRating), управлется авторами курса и администраторами
    """
    STATUSES = (
        ('review', _(u'На рассмотрении')),
        ('accepted', _(u'Принято')),
        ('declined', _(u'Отклонено')),
    )
    teacher = models.ForeignKey('plp.User', verbose_name=_(u'Пользователь, запросивший удаление'))
    csrating = models.ForeignKey('CourseStudentRating', verbose_name=_(u'Отзыв'))
    reason = models.TextField(verbose_name=_(u'Причина удаления'))
    resolution = models.CharField(max_length=15, verbose_name=_(u'Статус'), choices=STATUSES, default='review')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('teacher', 'csrating')
        verbose_name = _(u'Жалоба на отзыв о курсе')
        verbose_name_plural = _(u'Жалобы на отзыв о курсе')

    def __unicode__(self):
        return u'%s - %s' % (self.teacher, self.csrating)


class CourseStudentRatingQuestions(models.Model):
    """
    Вопрос по отзыву (CourseStudentRating), доступно авторам курса и администраторам.
    Текст вопроса отправляется пользователю, оставившему отзыв
    """
    teacher = models.ForeignKey('plp.User', verbose_name=_(u'Пользователь, отправивший вопрос'))
    csrating = models.ForeignKey('CourseStudentRating', verbose_name=_(u'Отзыв'))
    text = models.TextField(verbose_name=_(u'Текст вопроса'))

    class Meta:
        unique_together = ('teacher', 'csrating')
        verbose_name = _(u'Вопрос по отзыву')
        verbose_name_plural = _(u'Вопросы по отзывам')

    def __unicode__(self):
        return u'%s - %s' % (self.teacher, self.csrating)


class CourseFeedbackSettingsManager(models.Manager):
    def may_add_rating(self):
        """
        Проверка того, что добавление отзывов включено
        """
        if self.exists():
            return not self.first().disable_ratings
        return True

    def may_add_feedback(self):
        """
        Проверка того, что добавление историй включено
        """
        if self.exists():
            return not self.first().disable_feedbacks
        return True


class CourseFeedbackSettings(models.Model):
    """
    Глобальные настройки видимости отзывов и learner story для платформы
    """
    disable_ratings = models.BooleanField(verbose_name=_(u'Отключить временно добавление новых отзывов'), default=False)
    disable_feedbacks = models.BooleanField(verbose_name=_(u'Отключить временно добавление новых историй'), default=False)
    objects = CourseFeedbackSettingsManager()

    class Meta:
        verbose_name = _(u'Настройки отзывов')
        verbose_name_plural = _(u'Настройки отзывов')

course_feedback_published.connect(send_course_feedback_published_email)
course_feedback_created.connect(send_course_feedback_created_email, sender=CourseStudentFeedback)
course_rating_updated_or_created.connect(update_mean_ratings)
rating_claim_reviewed.connect(handle_rating_claim_reviewed)

### extend plp models

def rating_percentage(self):
    """
    возвращает список кортежей (оценка, процент проголосовавших, количество проголосовавших)
    """
    available_grades = range(5, 0, -1)
    grades = dict([(i, 0) for i in available_grades])
    csr = CourseStudentRating.objects.filter(session__course__id=self.id, status='published', declined=False)
    for item in csr:
        grades[item.rating] += 1
    result = []
    all_votes = float(sum(grades.values()))
    for i in available_grades:
        result.append((
            i, int(round(grades[i] * 100 / all_votes, 0)) if all_votes else 0, grades[i]
        ))
    return result


def review_count(self):
    return CourseStudentRating.objects.filter(session__course__id=self.id,
                                              status='published',
                                              declined=False).count()


def feedback_count(self):
    return CourseStudentFeedback.objects.filter(session__course__id=self.id,
                                                status='published').count()


setattr(Course, 'rating_percentage', rating_percentage)
setattr(Course, 'review_count', review_count)
setattr(Course, 'feedback_count', feedback_count)
