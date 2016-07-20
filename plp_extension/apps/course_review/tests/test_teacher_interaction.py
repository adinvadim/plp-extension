# coding: utf-8

import json
from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.core import mail
from django.template.loader import get_template
from plp.models import User, Course, CourseSession, University, Participant, CourseSessionAccessRole
from plp.roles import RoleBase
from plp_extension.apps.course_review.models import CourseStudentRating, CourseStudentRatingClaim, CourseStudentRatingQuestions


class TestCourseRatingTeacherInteraction(TestCase):
    """
    1. Я не имею прав автора курса и пытаюсь пожаловаться на курс - жалоба не создается
    2. Я имею права автора курса (в том числе staff)
    2.1. Я жалуюсь на отзыв о курсе, но не указываю причины жалобы - жалоба не создается
    2.2. Я жалуюсь на отзыв, на который я не жаловался - жалоба создается
    2.3. Я жалуюсь на отзыв, на который я уже жаловался
    2.3.1 Жалоба на рассмотрении - жалоба не создается
    2.3.2. Жалоба рассмотрена - жалоба не создается
    3.1. Я задаю вопрос, по отзыву, по которому не задавал вопрос - автору отзыва отправляется письмо с вопросом.
    3.2. Я задаю вопрос, по отзыву, по которому уже задавал вопрос - автору отзыва не отправляется письмо с вопросом.
    3.3. Я задаю вопрос, по отзыву на курс, где я не автор - автору отзыва не отправляется письмо с вопросом.
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

        self.teacher = User.objects.create_user('teacher', 'teacher@example.com', 'pass')
        teacher_role = RoleBase('staff', course_key='%s+%s+%s' % (university.slug, c.slug, self.session.slug))
        teacher_role.add_users(self.teacher)

        self.staff = User.objects.create_user('staff', 'staff@example.com', 'pass')
        self.staff.is_staff = True
        self.staff.save()

        Participant.objects.create(user=self.user, session=self.session)
        self.client = Client()
        self.url = reverse('handle-rating-claim')
        self.url_question = reverse('course-rating-question')

    def _create_claim(self, username, claims_cnt=1):
        """успешное создание жалобы"""
        self.client.login(username=username, password='pass')
        resp = self.client.post(self.url, data={'check_claim': self.csr.id})
        self.assertEqual(200, resp.status_code)
        resp_data = json.loads(resp.content)
        self.assertEqual(False, resp_data['claim_left'])
        resp = self.client.post(self.url, data={'rating_id': self.csr.id, 'reason': 'random reason'})
        self.assertEqual(200, resp.status_code)
        resp_data = json.loads(resp.content)
        self.assertEqual(0, resp_data['status'])
        self.assertEqual(claims_cnt, CourseStudentRatingClaim.objects.count())

    # 1.
    def test_user_without_rights_cant_create_rating_claim(self):
        self.client.login(username='user', password='pass')
        resp = self.client.post(self.url, data={'check_claim': self.csr.id})
        self.assertEqual(200, resp.status_code)
        resp_data = json.loads(resp.content)
        self.assertEqual(False, resp_data['claim_left'])
        resp = self.client.post(self.url, data={'rating_id': self.csr.id, 'reason': 'random reason'})
        self.assertEqual(403, resp.status_code)
        self.assertEqual(0, CourseStudentRatingClaim.objects.count())

    # 2.1
    def test_user_with_rights_cant_create_rating_claim_without_reason(self):
        for username in ['teacher', 'staff']:
            self.client.login(username=username, password='pass')
            resp = self.client.post(self.url, data={'check_claim': self.csr.id})
            self.assertEqual(200, resp.status_code)
            resp_data = json.loads(resp.content)
            self.assertEqual(False, resp_data['claim_left'])
            resp = self.client.post(self.url, data={'rating_id': self.csr.id})
            self.assertEqual(400, resp.status_code)
            self.assertEqual(0, CourseStudentRatingClaim.objects.count())

    # 2.2
    def test_user_with_rights_can_create_rating_claim(self):
        for cnt, username in enumerate(['teacher', 'staff'], 1):
            self._create_claim(username, cnt)

    # 2.3.1
    def test_user_with_rights_cant_claim_again(self):
        self._create_claim('teacher')

        resp = self.client.post(self.url, data={'check_claim': self.csr.id})
        self.assertEqual(200, resp.status_code)
        resp_data = json.loads(resp.content)
        self.assertEqual(True, resp_data['claim_left'])
        resp = self.client.post(self.url, data={'rating_id': self.csr.id, 'reason': 'random reason'})
        self.assertEqual(400, resp.status_code)
        self.assertEqual(1, CourseStudentRatingClaim.objects.count())

    # 2.3.2
    def test_user_with_rights_cant_claim_again2(self):
        self._create_claim('teacher')

        for resolution in ['accepted', 'declined']:
            CourseStudentRatingClaim.objects.update(resolution=resolution)
            resp = self.client.post(self.url, data={'check_claim': self.csr.id})
            self.assertEqual(200, resp.status_code)
            resp_data = json.loads(resp.content)
            self.assertEqual(True, resp_data['claim_left'])
            resp = self.client.post(self.url, data={'rating_id': self.csr.id, 'reason': 'random reason'})
            self.assertEqual(400, resp.status_code)
            self.assertEqual(1, CourseStudentRatingClaim.objects.count())

    # 3.1
    def test_user_with_rights_can_leave_question(self):
        self.client.login(username='teacher', password='pass')
        resp = self.client.post(self.url_question, data={'check_question': self.csr.id})
        self.assertEqual(200, resp.status_code)
        resp_data = json.loads(resp.content)
        self.assertEqual(False, resp_data['question_left'])
        resp = self.client.post(self.url_question, data={'rating_id': self.csr.id, 'text': 'random text'})
        self.assertEqual(200, resp.status_code)
        resp_data = json.loads(resp.content)
        self.assertEqual(0, resp_data['status'])
        self.assertEqual(1, CourseStudentRatingQuestions.objects.count())
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(1, len(email.get_recipients_emails()))
        self.assertIn(self.user.email, email.get_recipients_emails())
        self.assertDictContainsSubset({'Reply-To': self.teacher.email}, email._headers)
        self.assertEqual('emails/rating_question_message.html', email.get_html().template.name)
        self.assertEqual(get_template('emails/rating_question_subject.txt').render({'session': self.session}),
                         email.subject)

    # 3.2
    def test_user_cant_leave_question_again(self):
        CourseStudentRatingQuestions.objects.create(
            teacher=self.teacher,
            csrating=self.csr,
            text='random text'
        )
        self.client.login(username='teacher', password='pass')
        resp = self.client.post(self.url_question, data={'check_question': self.csr.id})
        self.assertEqual(200, resp.status_code)
        resp_data = json.loads(resp.content)
        self.assertEqual(True, resp_data['question_left'])
        resp = self.client.post(self.url_question, data={'rating_id': self.csr.id, 'text': 'random text2'})
        self.assertEqual(400, resp.status_code)
        self.assertEqual(1, CourseStudentRatingQuestions.objects.count())
        self.assertEqual('random text', CourseStudentRatingQuestions.objects.first().text)
        self.assertEqual(len(mail.outbox), 0)

    # 3.3
    def test_user_without_rights_cant_leave_question(self):
        CourseSessionAccessRole.objects.all().delete()
        self.client.login(username='teacher', password='pass')
        resp = self.client.post(self.url_question, data={'check_question': self.csr.id})
        self.assertEqual(200, resp.status_code)
        resp_data = json.loads(resp.content)
        self.assertEqual(False, resp_data['question_left'])
        resp = self.client.post(self.url_question, data={'rating_id': self.csr.id, 'text': 'random text'})
        self.assertEqual(403, resp.status_code)
        self.assertEqual(0, CourseStudentRatingQuestions.objects.count())
        self.assertEqual(len(mail.outbox), 0)
