# coding: utf-8

import json
import logging
from collections import OrderedDict
from operator import or_
from django.db.models import Q
from django.http import JsonResponse, HttpResponse, Http404
from django.views.generic import ListView
from django.views.decorators.http import require_POST
from django.core.exceptions import FieldError
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import ugettext as _
from plp_extension.apps.course_review.models import CourseStudentFeedback, CourseStudentRating, CourseStudentRatingClaim, \
    CourseFeedbackSettings, CourseStudentRatingQuestions
from plp_extension.apps.course_review.notifications import send_question_to_user
from plp_extension.apps.course_review.forms import FilterForm
from plp_extension.apps.course_review.signals import course_feedback_published, course_rating_updated_or_created, rating_claim_reviewed
from plp_extension.apps.course_review.utils import time_passed_since
from plp.models import CourseSession, CourseSessionAccessRole, Course, User, Participant
from plp.utils.helpers import access_role_required


class FeedbackModerationView(ListView):
    """
    Модерация learner story автором курса или администратором,
    отправка емейлов о публикации новой leaner story авторам курса
    """
    template_name = 'feedback_moderation.html'
    model = CourseStudentFeedback
    paginate_by = 10
    ordering = ['created_at']

    @method_decorator(access_role_required)
    def dispatch(self, request, *args, **kwargs):
        return super(FeedbackModerationView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        filter_dict = {'status': 'review'}
        if self.request.GET.get('feedback'):
            filter_dict['id'] = self.request.GET['feedback']
        elif self.request.GET.get('session'):
            filter_dict['session__id'] = self.request.GET['session']
        elif self.request.GET.get('university'):
            filter_dict['session__course__university__slug'] = self.request.GET['university']
        q = super(FeedbackModerationView, self).get_queryset().filter(**filter_dict)
        additional_filters = self.get_filter_for_user()
        if additional_filters:
            q = q.filter(additional_filters)
        return q

    def get_filter_for_user(self):
        user = self.request.user
        if user.is_staff:
            return []
        qs = []
        for course_key in user.get_access_course_tuples():
            qs.append(Q(
                session__course__university__slug=course_key[0],
                session__course__slug=course_key[1],
                session__slug=course_key[2],
            ))
        return reduce(lambda x, y: or_(x, y), qs, CourseStudentFeedback.objects.none())

    def get_context_data(self, **kwargs):
        context = super(FeedbackModerationView, self).get_context_data(**kwargs)
        form = FilterForm(self.request.GET, user=self.request.user)
        context['filter_form'] = form
        context['UNIV_CHOICES'] = form.UNIV_CHOICES
        context['SESSION_CHOICES'] = form.SESSION_CHOICES
        return context

    def post(self, request):
        accept = request.POST.get('accept')
        feedback_id = request.POST.get('feedback')
        if accept.lower() == 'true':
            new_status = 'published'
        else:
            new_status = 'rejected'
        updated = CourseStudentFeedback.objects.filter(id=feedback_id, status='review').update(status=new_status)
        if updated:
            csf = CourseStudentFeedback.objects.get(id=feedback_id, status=new_status)
            if new_status == 'published':
                if not CourseStudentFeedback.objects.get(id=feedback_id).published_at:
                    CourseStudentFeedback.objects.filter(id=feedback_id).update(published_at=timezone.now())
                msg = _(u'Преподаватель %(instructor)s опубликовал отзыв пользователя %(user)s %(f_id)s по курсу %(univ)s %(course)s %(session)s')
            else:
                msg = _(u'Преподаватель %(instructor)s отклонил отзыв пользователя %(user)s %(f_id)s по курсу %(univ)s %(course)s %(session)s')
            logging.info(msg % {
                'instructor': request.user.username,
                'user': csf.user.username,
                'univ': csf.session.course.university.title,
                'course': csf.session.course.title,
                'session': csf.session.slug,
                'f_id': csf.id
            })
        if updated and new_status == 'published':
            course_feedback_published.send(None, instance=csf)
        return JsonResponse({'status': 0 if updated else 1})


@require_POST
@login_required
def rate_course(request, course_session_id):
    """
    Получение и валидация отзыва по курсу от пользователя, апдейт средних оценок сессии и курса
    """
    try:
        session = CourseSession.objects.get(id=course_session_id)
    except CourseSession.DoesNotExist:
        return JsonResponse({'status': 1, 'reason': _(u'Сессия не найдена')})
    value = request.POST.get('rating')
    text = request.POST.get('comment', '')
    pros = request.POST.get('pros', '')
    cons = request.POST.get('cons', '')
    anon = request.POST.get('anon')
    anon = anon in (True, 'True', 'true', '1', 'on')
    rating = CourseStudentRating(
        user=request.user,
        session=session,
        rating=value,
        comment=text,
        anon=anon,
        pros=pros,
        cons=cons,
    )
    try:
        rating.clean_fields()
    except ValidationError as e:
        print e
        return JsonResponse({'status': 2, 'reason': _(u'Переданы некорректные данные')})
    try:
        csr = CourseStudentRating.objects.get(user=request.user, session=session)
        if csr.declined:
            return JsonResponse({'status': 4, 'reason': _(u'Ваш отзыв был удален по требованию автора курса')})
        old_value = csr.rating
        old_text = csr.comment
        csr.rating = value
        csr.comment = text
        csr.pros = pros
        csr.cons = cons
        csr.anon = anon
        csr.save()
        msg = _(u'Пользователь %(user)s изменил оценку %(old_value)s с отзывом %(old_text)s на %(value)s с отзывом %(text)s курсу %(univ)s %(course)s %(session)s')
        logging.info(msg % {
            'user': request.user.username,
            'value': value,
            'text': text,
            'univ': session.course.university.title,
            'course': session.course.title,
            'session': session.slug,
            'old_text': old_text,
            'old_value': old_value,
        })
        if session.rating_enabled:
            course_rating_updated_or_created.send(None, instance=csr, updated=True, value=value, old_value=old_value)
    except CourseStudentRating.DoesNotExist:
        status = 'published' if CourseFeedbackSettings.objects.may_add_rating() else 'waiting'
        csr = CourseStudentRating.objects.create(user=request.user, session=session, rating=value, comment=text,
                                                 anon=anon, status=status, pros=pros, cons=cons)
        msg = _(u'Пользователь %(user)s поставил оценку %(value)s с отзывом %(text)s курсу %(univ)s %(course)s %(session)s')
        logging.info(msg % {
            'user': request.user.username,
            'value': value,
            'text': text,
            'univ': session.course.university.title,
            'course': session.course.title,
            'session': session.slug,
        })
        if status != 'waiting':
            course_rating_updated_or_created.send(None, instance=csr, updated=False, value=value, old_value=0)
    return JsonResponse({'status': 0})


@require_POST
@login_required
def leave_course_feedback(request, course_session_id):
    """
    Получение и валидация learner story
    """
    try:
        session = CourseSession.objects.get(id=course_session_id)
    except CourseSession.DoesNotExist:
        return JsonResponse({'status': 1, 'reason': _(u'Сессия не найдена')})
    try:
        data = dict(request.POST.items())
    except (TypeError, KeyError, ValueError):
        return JsonResponse({'status': 4, 'reason': _(u'Переданы некорректные данные')})
    anon = request.POST.get('anon')
    anon = anon in (True, 'True', 'true', '1', 'on')
    try:
        existing = CourseStudentFeedback.objects.get(session=session, user=request.user)
    except CourseStudentFeedback.DoesNotExist:
        existing = None
    if existing and not existing.can_edit():
        return JsonResponse({'status': 3, 'reason': _(u'Вы не можете изменить оставленную историю прохождения')})
    feedback = CourseStudentFeedback(
        user=request.user,
        session=session,
        data=data,
        anon=anon,
        grade=0,  # чтобы прошла валидация, при сохранении подставится значение из certificate_data
    )
    try:
        feedback.clean_fields()
    except ValidationError as e:
        return JsonResponse({'status': 2, 'reason': _(u'Переданы некорректные данные')})
    if existing:
        existing.data = data
        existing.anon = anon
        existing.status = 'review'
        existing.save()
    else:
        feedback.save()
    return JsonResponse({'status': 0})


class CourseRatingView(ListView):
    """
    Отображение страницы отзывов на конкретную сессию курса
    """
    ordering = ['-updated_at']
    model = CourseStudentRating
    template_name = 'course_rating.html'

    def get_object(self):
        return get_object_or_404(CourseSession,
                                 course__university__slug=self.kwargs['uni_slug'],
                                 course__slug=self.kwargs['course_slug'],
                                 slug=self.kwargs['session_slug'])

    def get_queryset(self):
        session = self.get_object()
        if not session.rating_enabled:
            if not CourseSessionAccessRole.objects.has_session_access(self.request.user, session):
                raise Http404
            return self.model.objects.none()
        return super(CourseRatingView, self).get_queryset().filter(session=session, declined=False, status='published')

    def get_context_data(self, **kwargs):
        context = super(CourseRatingView, self).get_context_data(**kwargs)
        session = self.get_object()
        context['session'] = session
        user = self.request.user
        context['is_author'] = CourseSessionAccessRole.objects.has_session_access(user, session)
        context['rating_enabled'] = session.rating_enabled
        return context


class CourseRatingByDateView(ListView):
    """
    Страница отзывов на все сессии заданного курса за определенный день
    """
    ordering = ['session__slug', '-updated_at']
    model = CourseStudentRating
    template_name = 'course_by_date_rating.html'

    def get_object(self):
        return get_object_or_404(Course,
                                 slug=self.kwargs['course_slug'],
                                 university__slug=self.kwargs['uni_slug'])

    def get_requested_date(self):
        year, month, day = self.kwargs['date'].split('_')
        try:
            return timezone.now().date().replace(year=int(year), month=int(month), day=int(day))
        except ValueError:
            raise Http404

    def get_queryset(self):
        current_date = self.get_requested_date()
        q = super(CourseRatingByDateView, self).get_queryset()
        q = q.filter(
            declined=False,
            status='published',
            session__rating_enabled=True,
            updated_at__gte=timezone.datetime.combine(current_date, timezone.datetime.min.time()),
            updated_at__lte=timezone.datetime.combine(current_date, timezone.datetime.max.time())
        )
        return q

    def get_context_data(self, **kwargs):
        context = super(CourseRatingByDateView, self).get_context_data(**kwargs)
        object_list = context['object_list']
        by_sessions = OrderedDict()
        is_author_cache = {}
        for csr in object_list:
            csr.is_author = is_author_cache.setdefault(
                csr.session.slug, CourseSessionAccessRole.objects.has_session_access(self.request.user, csr.session)
            )
            if csr.session.slug in by_sessions:
                by_sessions[csr.session.slug].append(csr)
            else:
                by_sessions[csr.session.slug] = [csr]
        context['by_sessions'] = by_sessions
        context['course'] = self.get_object()
        context['date'] = self.get_requested_date()
        return context


class TeacherCoursesRatingByDateView(ListView):
    """
    Отображение отзывов по всем курсам указанного пользователя, для которых он является автором,
    за конкретный день. Доступно самому пользователю и администраторам.
    """
    model = CourseStudentRating
    template_name = 'teacher_courses_rating_by_date.html'
    ordering = ['session__course__title', 'session__slug', '-updated_at']

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_staff or request.user.username == kwargs['username']:
            return super(TeacherCoursesRatingByDateView, self).dispatch(request, *args, **kwargs)
        raise Http404

    def get_requested_date(self):
        year, month, day = self.kwargs['date'].split('_')
        try:
            return timezone.now().date().replace(year=int(year), month=int(month), day=int(day))
        except ValueError:
            raise Http404

    def get_queryset(self):
        current_date = self.get_requested_date()
        user = get_object_or_404(User, username=self.kwargs['username'])
        qs = []
        for course_key in user.get_access_course_tuples():
            qs.append(Q(
                course__university__slug=course_key[0],
                course__slug=course_key[1],
                slug=course_key[2],
            ))
        if qs:
            qs = reduce(lambda x, y: or_(x, y), qs)
        else:
            raise Http404
        session_ids = CourseSession.objects.filter(qs).values_list('id', flat=True)
        q = super(TeacherCoursesRatingByDateView, self).get_queryset()
        q = q.filter(
            declined=False,
            status='published',
            session__id__in=session_ids,
            session__rating_enabled=True,
            updated_at__gte=timezone.datetime.combine(current_date, timezone.datetime.min.time()),
            updated_at__lte=timezone.datetime.combine(current_date, timezone.datetime.max.time())
        )
        return q

    def get_context_data(self, **kwargs):
        context = super(TeacherCoursesRatingByDateView, self).get_context_data(**kwargs)
        object_list = context['object_list']
        by_sessions = OrderedDict()
        for csr in object_list:
            csr.is_author = True
            if csr.session in by_sessions:
                by_sessions[csr.session].append(csr)
            else:
                by_sessions[csr.session] = [csr]
        context['by_sessions'] = by_sessions
        context['user'] = User.objects.get(username=self.kwargs['username'])
        context['date'] = self.get_requested_date()
        return context


@require_POST
def handle_rating_claim(request):
    """
    Проверка того, оставлял ли пользователь жалобу на отзыв, если да, то добавляется сообщение
    о статусе рассмотрения жалобы.
    Получение и валидация жалоб на отзыв.
    """
    if request.POST.get('check_claim'):
        claim_id = request.POST['check_claim']
        csrc = CourseStudentRatingClaim.objects.filter(teacher=request.user, csrating__id=claim_id)
        if csrc:
            session = csrc[0].csrating.session
            if not CourseSessionAccessRole.objects.has_session_access(request.user, session):
                return HttpResponse(status=403)
            if csrc[0].resolution == 'review':
                text = _(u'Вы уже отправляли запрос на удаление отзыва %(dt)s с комментарием "%(comment)s". ' \
                       u'Пожалуйста, дождитесь его рассмотрение администратором платформы.')
                text = text % {
                    'dt': timezone.localtime(csrc[0].created_at).strftime('%d.%m.%Y %H:%M'),
                    'comment': csrc[0].reason
                }
            elif csrc[0].resolution == 'declined':
                text = _(u'Вы уже отправляли запрос на удаление отзыва %(dt)s с комментарием "%(comment)s". ' \
                       u'Администратор считает указанные вами причины для удаления отзыва недостаточными. ' \
                       u'По дополнительным вопросам вы можете связаться <a href="%(href)s">с нами</a>.')
                text = text % {
                    'dt': timezone.localtime(csrc[0].created_at).strftime('%d.%m.%Y %H:%M'),
                    'comment': csrc[0].reason,
                    'href': reverse('feedback')
                }
            else:
                text = _(u'Оценка была удалена')
            return JsonResponse({
                'claim_left': True,
                'text': text
            })
        return JsonResponse({'claim_left': False})

    rating_id = request.POST.get('rating_id')
    reason = request.POST.get('reason', '')
    if rating_id and reason.strip():
        try:
            rating = CourseStudentRating.objects.get(id=rating_id)
        except (CourseStudentRating.DoesNotExist, ValueError):
            return HttpResponse(status=400)
        if not CourseSessionAccessRole.objects.has_session_access(request.user, rating.session):
            return HttpResponse(status=403)
        if not CourseStudentRatingClaim.objects.filter(teacher=request.user, csrating=rating).exists():
            CourseStudentRatingClaim.objects.create(
                teacher=request.user,
                csrating=rating,
                reason=reason
            )
            return JsonResponse({'status': 0})
    return HttpResponse(status=400)


@require_POST
def handle_rating_question(request):
    """
    Проверка того, оставлял ли пользователь вопрос по отзыву, если да, то добавляется сообщение об этом.
    Получение и валидация вопросов по отзыву и отправка сообщения автору отзыва.
    """
    if request.POST.get('check_question'):
        question_id = request.POST['check_question']
        csrq = CourseStudentRatingQuestions.objects.filter(teacher=request.user, csrating__id=question_id)
        if csrq:
            if not CourseSessionAccessRole.objects.has_session_access(request.user, csrq[0].csrating.session):
                return HttpResponse(status=403)
            text = _(u'Вы уже отправляли вопрос "%(question)s" по данному отзыву')
            text = text % {'question': csrq[0].text}
            return JsonResponse({
                'question_left': True,
                'text': text
            })
        return JsonResponse({'question_left': False})

    rating_id = request.POST.get('rating_id')
    text = request.POST.get('text', '')
    if rating_id and text.strip():
        try:
            rating = CourseStudentRating.objects.get(id=rating_id)
            assert not rating.anon
        except (CourseStudentRating.DoesNotExist, ValueError, AssertionError):
            return HttpResponse(status=400)
        if not CourseSessionAccessRole.objects.has_session_access(request.user, rating.session):
            return HttpResponse(status=403)
        if not CourseStudentRatingQuestions.objects.filter(teacher=request.user, csrating=rating).exists():
            csrq = CourseStudentRatingQuestions.objects.create(
                teacher=request.user,
                csrating=rating,
                text=text
            )
            send_question_to_user(csrq)
            msg = _(u'Teacher %(user_id)s sent question %(text)s about %(course_student_rating_id)s')
            logging.info(msg % {
                'user_id': request.user.id,
                'text': text,
                'course_student_rating_id': rating.id,
            })
            return JsonResponse({'status': 0})
    return HttpResponse(status=400)


class RatingClaimModerationView(ListView):
    """
    Модерация жалоб на отзывы по курсам. Доступно администраторам. Апдейт средних оценок сессии и курса.
    """
    template_name = 'rating_claim_moderation.html'
    model = CourseStudentRatingClaim
    paginate_by = 10
    ordering = ['created_at']

    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super(RatingClaimModerationView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        filter_dict = {'resolution': 'review'}
        if self.request.GET.get('feedback'):
            filter_dict['id'] = self.request.GET['feedback']
        elif self.request.GET.get('session'):
            filter_dict['csrating__session__id'] = self.request.GET['session']
        elif self.request.GET.get('university'):
            filter_dict['csrating__session__course__university__slug'] = self.request.GET['university']
        q = super(RatingClaimModerationView, self).get_queryset().filter(**filter_dict).select_related('csrating')
        return q

    def get_context_data(self, **kwargs):
        context = super(RatingClaimModerationView, self).get_context_data(**kwargs)
        form = FilterForm(self.request.GET, user=self.request.user)
        context['filter_form'] = form
        context['UNIV_CHOICES'] = form.UNIV_CHOICES
        context['SESSION_CHOICES'] = form.SESSION_CHOICES
        return context

    def post(self, request):
        accept = request.POST.get('accept')
        feedback_id = request.POST.get('feedback')
        if accept.lower() == 'true':
            new_status = 'accepted'
        else:
            new_status = 'declined'
        updated = CourseStudentRatingClaim.objects.filter(id=feedback_id, resolution='review').update(
            resolution=new_status)
        if updated and new_status == 'accepted':
            csrc = CourseStudentRatingClaim.objects.get(id=feedback_id, resolution=new_status)
            CourseStudentRating.objects.filter(id=csrc.csrating.id).update(declined=True)
            course_rating_updated_or_created.send(None,
                                                  instance=csrc.csrating,
                                                  updated=False,
                                                  deleted=True,
                                                  value=0,
                                                  old_value=csrc.csrating.rating)
        if updated:
            msg = _(u'staff user %(user)s set resolution %(resolution)s for rating claim %(rating_claim_id)s')
            logging.info(msg % {
                'user': request.user.username,
                'resolution': new_status,
                'rating_claim_id': feedback_id,
            })
            rating_claim_reviewed.send(None, instance=CourseStudentRatingClaim.objects.get(id=feedback_id))
        return JsonResponse({'status': 0 if updated else 1})


@require_POST
def course_rating_and_feedback_list(request, course_id):
    """
    Фильтрация отзывов и историй по курсу. Параметры:
    limit - количество возвращаемых отзывов/историй
    offset
    student_type - "student" или "graduate"
    rating - оценка отзыва от 1 до 5
    order_by - "rating_asc", "rating_desc", "session_asc", "session_desc", "date_asc", "date_desc"
    session - id сессии
    """
    course = get_object_or_404(Course, id=course_id)
    params = request.POST
    try:
        limit = int(params.get('limit', 3))
    except (ValueError, TypeError):
        limit = 3
    try:
        offset = int(params.get('offset', 0))
    except (ValueError, TypeError):
        offset = 0
    student_type = params.get('student_type')
    session = params.get('session')
    try:
        rating = int(params.get('rating'))
    except (ValueError, TypeError):
        rating = None
    order_by = params.get('order_by')
    filter_dict = {
        'session__course__id': course_id
    }
    if session:
        filter_dict['session__id'] = session
    if rating is not None:
        filter_dict['rating'] = rating

    ratings = CourseStudentRating.objects.filter(declined=False, status='published', **filter_dict)
    if student_type in ['student', 'graduate']:
        graduates = Participant.objects.filter(session__in=course.course_sessions.all(), is_graduate=True).\
            values_list('session__slug', 'user__username')
        graduates_by_session = {}
        for i in graduates:
            graduates_by_session[i[0]] = graduates_by_session.get(i[0], []) + [i[1]]
        Q_filter = [Q(session__slug=k, user__username__in=v) for k, v in graduates_by_session.iteritems()]
        if Q_filter:
            Q_filter = reduce(lambda x, y: or_(x, y), Q_filter)
            ratings = ratings.filter(Q_filter) if student_type == 'graduate' else ratings.exclude(Q_filter)
        else:
            ratings = CourseStudentRating.objects.none() if student_type == 'graduate' else ratings

    try:
        assert not (student_type and student_type == 'graduate')
        feedbacks = CourseStudentFeedback.objects.filter(status='published', **filter_dict)
    except (FieldError, AssertionError):
        feedbacks = CourseStudentFeedback.objects.none()

    if order_by in ['rating_asc', 'rating_desc']:
        ratings = ratings.order_by('rating' if order_by == 'rating_asc' else '-rating')
        combined = list(ratings) + list(feedbacks)
    elif order_by in ['session_asc', 'session_desc']:
        if order_by == 'session_desc':
            dt_for_none = timezone.make_aware(timezone.datetime(1000, 1, 1))
        else:
            dt_for_none = timezone.make_aware(timezone.datetime(9999, 1, 1))
        combined = sorted(list(ratings) + list(feedbacks),
                          key=lambda x: x.session.datetime_starts if x.session.datetime_starts else dt_for_none)
        if order_by == 'session_desc':
            combined.reverse()
    else:
        if order_by not in ['date_asc', 'date_desc']:
            order_by = 'date_desc'
        combined = sorted(list(ratings) + list(feedbacks), key=lambda x: x.updated_at)
        if order_by == 'date_desc':
            combined.reverse()

    count = len(combined)
    combined = combined[offset:limit+offset]
    result = []
    tmp = {}
    for item in combined:
        tmp = {
            'anon': item.anon,
            'user': item.user.get_full_name() if not item.anon else '',
            'date': time_passed_since(item.updated_at),
            'session_id': item.session.id
        }
        if isinstance(item, CourseStudentRating):
            tmp.update({
                'type': 'r',
                'rating': item.rating,
                'comment': item.comment,
                'pros': item.pros,
                'cons': item.cons,
            })
        else:
            tmp.update({
                'type': 'f',
                'comment_why': (item.data or {}).get('comment_why', ''),
                'comment_new': (item.data or {}).get('comment_new', ''),
                'comment_advise': (item.data or {}).get('comment_advise', ''),
                'comment_suggest': (item.data or {}).get('comment_suggest', ''),
                'comment': (item.data or {}).get('comment', ''),
            })
        result.append(tmp)
    return JsonResponse({'items': result, 'items_count': count})


def course_rating_page(request, uni_slug, slug):
    course = get_object_or_404(Course, slug=slug, university__slug=uni_slug)
    # если курс скрыт - страницу могут просматривать записанные на него пользователи и staff
    if course.status == 'hidden':
        user = request.user
        if not user.is_authenticated() or (not course.is_user_enrolled(user) and not user.is_staff):
            raise Http404
    is_graduate = request.user.is_authenticated() and \
                  Participant.objects.filter(session__in=course.course_sessions.all(),
                                             user=request.user,
                                             is_graduate=True).exists()
    session = course.next_session
    status = session.button_status(request.user) if session else course.button_status(request.user)
    return render(request, 'course_reviews.html', {'object': course, 'is_graduate': is_graduate,
                                                   'session': session,
                                                   'status': status,
                                                   'all_sessions': course.all_sessions(),
                                                   'authenticated': request.user.is_authenticated() })


@login_required
def leave_course_rating_view(request, uni_slug, course_slug, session_slug):
    session = get_object_or_404(CourseSession,
                                course__university__slug=uni_slug,
                                course__slug=course_slug,
                                slug=session_slug)

    initial_data = {}
    moderation_status = None
    can_edit = True
    # Для отличия истории от отзыва в шаблоне
    if Participant.objects.filter(user=request.user, session=session, is_graduate=True):
        finished = True
        try:
            feedback = CourseStudentFeedback.objects.get(user=request.user, session=session)
            initial_data = feedback.data
            moderation_status = feedback.status
            can_edit = feedback.can_edit()
        except CourseStudentFeedback.DoesNotExist:
            pass
    else:
        finished = False
        try:
            item = CourseStudentRating.objects.get(user=request.user, session=session)
            initial_data = item
            moderation_status = item.status
            can_edit = item.can_edit()
        except CourseStudentRating.DoesNotExist:
            pass

    rating = request.GET.get('rating', '')
    status = session.button_status(request.user)
    context = {
        'object' : session.course,
        'session': session,
        'finished': finished,
        'rating': rating,
        'status': status,
        'initial_data': initial_data,
        'moderation_status': moderation_status,
        'can_edit': can_edit,
    }

    return render(request, 'leave_rating.html', context)


@login_required
def thanks_for_review(request, uni_slug, course_slug, session_slug):
    session = get_object_or_404(CourseSession,
                                course__university__slug=uni_slug,
                                course__slug=course_slug,
                                slug=session_slug)
    context = {
        'session': session,
        'status': session.button_status(request.user),
        'finished': Participant.objects.filter(user=request.user, session=session, is_graduate=True).exists()
    }
    return render(request, 'thanks_for_review.html', context)
