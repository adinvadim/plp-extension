# coding: utf-8

import json
from functools import update_wrapper
from django.contrib import admin
from django.conf.urls import url as _url
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.template.response import TemplateResponse
from plp_extension.apps.pse.pse_admin import admin_site as pse_admin_site, ModelAdminWithReadOnly as PSEModelAdmin
from statistics.models import EnrollmentStatsCourseSession
from plp.admin import CourseAdmin, CourseUniversityFilter, CustomCourseCangeList, university_name
from plp.models import Participant, EnrollmentReason, Course


class PSECourseAdmin(CourseAdmin):
    actions = None
    inlines = []
    course_statistics_template = 'pse/plp/course/course_statistics.html'
    change_form_template = 'pse/plp/course/change_form.html'

    def image_tag(self, obj):
        return u'<a href="%s"><img src="%s"     style="max-width: 275px; max-height: 155px;" /></a>' % (
            reverse('pse:%s_%s_change' % (obj._meta.app_label, obj._meta.model_name), args=(obj.id,)),
            u"{}{}".format(settings.MEDIA_URL, obj.cover)
        )
    image_tag.short_description = _(u'Картинка курса')
    image_tag.allow_tags = True

    @staticmethod
    def has_add_permission(self):
        return False

    def get_urls(self):
        urls = super(CourseAdmin, self).get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            return update_wrapper(wrapper, view)

        custom_urls = [
            _url(r'^statistics/$', wrap(self.statistics_view), name='%s_%s_statistics' % info),
            _url(r'^(.+)/statistics/$', wrap(self.course_statistics_view), name='%s_%s_course_stat' % info),
        ]
        return custom_urls + urls

    def statistics_view(self, request):
        return self.changelist_view(request)

    def get_list_filter(self, request):
        if self.statistics_requested(request):
            return [CourseUniversityFilter]
        return super(CourseAdmin, self).get_list_filter(request)

    def statistics_requested(self, request):
        info = self.model._meta.app_label, self.model._meta.model_name
        check_path = reverse('pse:%s_%s_statistics' % info)
        return request.path == check_path

    def get_actions(self, request):
        if self.statistics_requested(request):
            return None
        return super(CourseAdmin, self).get_actions(request)

    def last_session_participants(self, obj):
        session = obj.next_session
        if session:
            return Participant.objects.filter(session=session).count()
        return 0
    last_session_participants.short_description = _(u'Зарегистрировано на последнюю сессию курса')

    def verified_count(self, obj):
        session = obj.next_session
        if session:
            return EnrollmentReason.objects.filter(participant__session=session,
                                                   session_enrollment_type__mode='verified').count()
        return 0
    verified_count.short_description = _(u'С прохождением в режиме подтверждения личности')

    def get_changelist(self, request, **kwargs):
        if self.statistics_requested(request):
            return CustomCourseCangeList
        return super(CourseAdmin, self).get_changelist(request, **kwargs)

    def course_statistics_view(self, request, obj_id):
        obj = self.get_object(request, obj_id)
        session = obj.next_session
        start_date, end_date, enrollment_data, payment_data = None, None, [], []
        if session:
            enrs = EnrollmentStatsCourseSession.objects.filter(
                session_slug=session.slug,
                course_slug=obj.slug,
                university_slug=obj.university.slug,
                time_to__lte=timezone.now().replace(hour=0)
            ).values_list('time_from', 'count')
            enrs = dict([(timezone.localtime(i[0]), i[1]) for i in enrs])
            enr_data = {}
            for k, v in enrs.iteritems():
                enr_data[k.date()] = enr_data.get(k.date(), 0) + v
            for i in sorted(enr_data.keys()):
                count = (enrollment_data[-1][1] if enrollment_data else 0) + enr_data[i]
                enrollment_data.append([i.strftime('%Y-%m-%d'), count])

            payments = {}
            for i in EnrollmentReason.objects.filter(participant__session=session,
                    session_enrollment_type__mode='verified').values_list('_ctime', flat=True):
                day = timezone.localtime(i).date()
                payments[day] = payments.get(day, 0) + 1
            for i in sorted(payments.keys()):
                count = (payment_data[-1][1] if payment_data else 0) + payments[i]
                payment_data.append([i.strftime('%Y-%m-%d'), count])

        return TemplateResponse(request, self.course_statistics_template, {
            'course': obj,
            'enrollment_data': json.dumps(enrollment_data),
            'payment_data': json.dumps(payment_data),
            'participants_count': Participant.objects.filter(session=session).count() if session else 0,
            'payments_count': payment_data[-1][1] if payment_data else 0,
        })

    def get_list_display(self, request):
        if self.statistics_requested(request):
            return (
                'title', 'slug', 'last_session_participants', 'verified_count'
            )
        return (
            'image_tag', 'title', 'slug', 'status', university_name, 'abs_url',
        )

    @staticmethod
    def get_fields(self, request, obj=None):
        return (
            'slug', 'title', 'cover', 'description', 'about', 'course_format', 'links', 'syllabus',
            'specifications', 'results', 'workload', 'points', 'status', 'recommended',
        )

    fieldsets = [
        (_(u'Название курса'), {
            'fields': ('title',),
            'description': u'<div class="help">{}</div>'.format(
                _(u'Для изменения названия курса пожалуйста обратитесь в службу '
                u'поддержки. Этот вопрос требует согласования')
            ),
        }),
        (_(u'Код курса'), {
            'fields': ('slug',),
            'description': u'<div class="help">{}</div>'.format(
                _(u'Код курса не может быть изменен в обычных условиях. Если же вам '
                u'по каким-то причинам нужно его изменить - пожалуйста обратитесь в службу поддержки')
            ),
        }),
        (_(u'Обложка курса'), {
            'fields': ('cover', 'image_tag'),
            'description': u'<div class="help">{}</div>'.format(
                _(u'Используйте изображения правами на которые вы обладаете, или '
                u'которые могут быть использованы в составе образовательных рессурсов')
            ),
        }),
        (_(u'Описание курса'), {
            'fields': ('description',),
            'description': u'<div class="help">{}</div><div class="quiet small"><div>{}</div>{}</div>'.format(
                _(u'Постарайтесь кратко, в двух предложениях описать что это за курс и кому он может быть полезен.'),
                _(u'Пример:'),
                _(u'Курс ориентирован на освоение технологий и техник самоменеджмента для достижения '
                u'профессиональных и личных целей обучаемых. Рассматриваются практические методы '
                u'управления деятельностью и временем в разных сферах жизни, развития личностного '
                u'потенциала, способы принятия решения, планирования процессов, развития карьеры, '
                u'работы в команде и эффективного общения.'))
        }),
        (_(u'О курсе'), {
            'fields': ('about',),
            'description': u'<div class="help">{}</div>'.format(
                _(u'Тут вы можете указать более подробную информацию о целях, задачах и особенностях курса')
            )
        }),
        (_(u'Формат курса'), {
            'fields': ('course_format',),
            'description': u'<div class="help">{}</div><div class="quiet small"><div>{}</div>{}</div>'.format(
                _(u'Опишите формат курса в разрезе его структуры и в разрезе используемой системы оценивания'),
                _(u'Пример:'),
                _(u'Курс состоит из 10 недель лекций и 1 недели экзамена. Каждую неделю слушатель '
                u'выполняет задания, составляющие 10% от всего курса (5% тест и 5% задачи с '
                u'ответом). Экзамен также состоит из теста и задач с ответом, каждая часть '
                u'оценивается в 15% от общей суммы. Для успешного прохождения курса необходимо '
                u'в каждом задании набрать не менее 50% от общего числа баллов.')
            )
        }),
        (_(u'Внешние ресурсы'), {
            'fields': ('links',),
            'description': u'<div class="help">{}</div>'.format(
                _(u'Укажите название и ссылки ресурсов, которые могут быть полезны '
                u'при изучении курса (другие электронные курсы, книги, публикации, итд')
            )
        }),
        (_(u'Программа курса'), {
            'fields': ('syllabus',),
            'description': u'<div class="help">{}</div>'.format(
                _(u'Понедельная программа курса с указанием тем и подтем')
            )
        }),
        (_(u'Требования'), {
            'fields': ('specifications',),
            'description': u'<div class="help">{}</div><div class="quiet small"><div>{}</div>{}</div>'.format(
                _(u'Укажите требования предъявляемые к слушателям курса и необходимые для его успешного освоения'),
                _(u'Пример:'),
                _(u'Для участия в курсе слушателю необходимо иметь базовые представления о теории '
                u'множеств и началах анализа. Все остальные понятия будут введены в ходе курса.')
            )
        }),
        (_(u'Результаты обучения'), {
            'fields': ('results',),
            'description': u'<div class="help">{}</div>'.format(
                _(u'Пожалуйста, перечислите результаты обучения которыми учащийся '
                u'может овладеть в процессе обучения на курсе')
            )
        }),
        (_(u'Часов в неделю'), {
            'fields': ('workload',),
            'description': u'<div class="help">{}</div>'.format(
                _(u'Какое примерно количество часов в неделю требуется среднему '
                u'ученику для обучения на курсе (просмотра видеолекций, выполнения заданий и '
                u'общения на форуме)')
            )
        }),
        (_(u'Зачётных единиц'), {
            'fields': ('points',),
            'description': u'<div class="help">{}</div>'.format(
                _(u'Какое количество зачетных единиц рекомендуют перезачитывать авторы курса')
            )
        }),
        (_(u'Статус видимости'), {
            'fields': ('status',),
            'description': u'<div class="help">{}</div>'.format(
                _(u'Если флаг выставлен - то курс видим в каталоге, если флаг не '
                u'установлен - курс доступен только по прямо ссылке')
            )
        }),
        (_(u'Флаг рекомендованный курс'), {
            'fields': ('recommended',),
            'description': u'<div class="help">{}</div>'.format(
                _(u'Если флаг установлен, то курс будет использоваться при ротации курсов на главной странице')
            )
        }),
    ]

    @staticmethod
    def get_readonly_fields(self, request, obj=None):
        return 'slug', 'title', 'image_tag',


@admin.register(Course, site=pse_admin_site)
class PSECustomCourseAdmin(PSECourseAdmin, PSEModelAdmin):
    pass
