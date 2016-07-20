# coding: utf-8

from operator import or_
from django.db.models import Q
from django import forms
from django.utils.translation import ugettext_lazy as _
from plp.models import CourseSession, University


class FilterForm(forms.Form):
    """
    Форма с вариантами выбора вузов и сессий, к которым у пользователя есть доступ
    """
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(FilterForm, self).__init__(*args, **kwargs)
        univs = University.objects.order_by('title')
        sessions = CourseSession.objects.order_by('course__university__title', 'course__title', 'slug')
        if not user.is_staff:
            filter_sessions, filter_universities = [], []
            for course_key in user.get_access_course_tuples():
                filter_sessions.append(Q(
                    course__university__slug=course_key[0],
                    course__slug=course_key[1],
                    slug=course_key[2],
                ))
                q = Q(slug=course_key[0])
                if q not in filter_universities:
                    filter_universities.append(q)
            filter_universities = reduce(lambda x, y: or_(x, y), filter_universities, University.objects.none())
            filter_sessions = reduce(lambda x, y: or_(x, y), filter_sessions, CourseSession.objects.none())
            univs = univs.filter(filter_universities)
            sessions = sessions.filter(filter_sessions)

        self.UNIV_CHOICES = [('', _(u'Все'))] + list(univs.values_list('slug', 'title'))
        self.SESSION_CHOICES = [('', _(u'Все'))] + [
            (i[0], u'%(univ)s %(course)s %(session)s' % {'univ': i[1], 'course': i[2], 'session': i[3]}) for i in
                sessions.values_list('id', 'course__university__title', 'course__title', 'slug')
        ]
        self.fields['university'].choices = self.UNIV_CHOICES
        self.fields['session'].choices = self.SESSION_CHOICES

    university = forms.ChoiceField(label=_(u'Фильтрация по вузу'), required=False,
                                   widget=forms.Select(attrs={'autocomplete': 'off'}))
    session = forms.ChoiceField(label=_(u'Фильтрация по сессии курса'), required=False,
                                widget=forms.Select(attrs={'autocomplete': 'off'}))
