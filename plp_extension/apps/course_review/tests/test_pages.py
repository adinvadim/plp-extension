# coding: utf-8

from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from plp.models import User, University, CourseSession, Course, Participant
from plp.roles import RoleBase
from plp_extension.apps.course_review.models import CourseStudentRating


class TestCourseUserByDayView(TestCase):
    """
    1. Я пользователь без прав и пытаюсь увидеть страницу отзывов за день, получаю 404
    2. Я пользователь с правами на курс и пытаюсь посмотреть не свою страницу отзывов, получаю 404.
    3. Я пользователь с правами на курс и пытаюсь посмотреть свою страницу отзывов за день, получаю 200
    4. Я админ и пытаюсь посмотреть страницу для другого преподавателя, получаю 200
    """
    def setUp(self):
        university = University.objects.create(
            slug='univ',
            abbr='abbr',
            title='University'
        )
        c = Course.objects.create(
            slug='c',
            university=university,
            status='published',
            title='course'
        )
        self.course = c
        self.session = CourseSession.objects.create(
            slug='cs',
            course=c
        )
        self.user = User.objects.create_user('user', 'user@example.com', 'pass')
        self.csr = CourseStudentRating.objects.create(
            user=self.user,
            session=self.session,
            rating=4
        )
        self.rating_date = self.csr.updated_at.strftime('%Y_%m_%d')

        self.teacher1 = User.objects.create_user('teacher1', 'teacher1@example.com', 'pass')
        self.teacher2 = User.objects.create_user('teacher2', 'teacher2@example.com', 'pass')
        teacher_role = RoleBase('staff', course_key='%s+%s+%s' % (university.slug, c.slug, self.session.slug))
        teacher_role.add_users(self.teacher1, self.teacher2)

        self.staff = User.objects.create_user('staff', 'staff@example.com', 'pass')
        self.staff.is_staff = True
        self.staff.save()

        self.url = reverse('teacher-course-rating-by-date', kwargs={'username': self.teacher1.username,
                                                                          'date': self.rating_date})

        Participant.objects.create(user=self.user, session=self.session)
        self.client = Client()

    # 1.
    def test_user_without_rights_cant_view_page(self):
        self.client.login(username=self.user.username, password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(404, resp.status_code)

    # 2.
    def test_user_with_rights_cant_view_someone_elses_page(self):
        self.client.login(username=self.teacher2.username, password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(404, resp.status_code)

    # 3.
    def test_user_with_rights_can_view__his_page(self):
        self.client.login(username=self.teacher1.username, password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(200, resp.status_code)

    # 4.
    def test_staff_can_view_page(self):
        self.client.login(username=self.staff.username, password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(200, resp.status_code)
