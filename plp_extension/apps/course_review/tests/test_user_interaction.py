# coding: utf-8

import json
from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from plp.models import User, Course, CourseSession, University, Participant
from plp_extension.apps.course_review.models import CourseStudentRating


class TestCourseRatingUserInteraction(TestCase):
    """
    1. Я не записан на курс, пробую оставить отзыв на курс, отзыв не добавляется
    2. Я записан на курс
    2.1. Пробую добавить отзыв с оценкой больше 2, без текста, отзыв добавлен
    2.2.1. Пробую добавить отзыв с оценкой меньше 3 без текста - отзыв не добавлен
    2.2.2. Пробую добавить отзыв с оценкой меньше 3 текст 100000 символов - отзыв не добавлен
    2.2.3. Пробую добавить отзыв с оценкой меньше 3 текст 1000 символов - отзыв не добавлен
    2.2.4. Пробую добавить отзыв с оценкой меньше 3 текст 100 символов - отзыв не добавлен
    2.3 Я пробую добавить отзыв на курс, мой отзыв на курс удален по требованию автора курса. Я не могу добавить отзыв
    2.4. Я изменил оценку курса на отрицательную, но не добавил текст отзыва - оценка не изменилась
    2.5. Я изменил оценку, правильным образом изменилась средняя оценка курса и сессии курса
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
        Participant.objects.create(user=self.user, session=self.session)
        self.client = Client()
        self.client.login(username='user', password='pass')
        self.url = reverse('rate-course', kwargs={'course_session_id': self.session.id})

    # 1.
    def test_unenrolled_user_cant_leave_rating(self):
        Participant.objects.all().delete()
        resp = self.client.post(self.url, data={'value': 3})
        self.assertEqual(200, resp.status_code)
        resp_data = json.loads(resp.content)
        self.assertNotEqual(0, resp_data['status'])
        self.assertEqual(0, CourseStudentRating.objects.count())

    # 2.1
    def test_add_rating_gt_2(self):
        resp = self.client.post(self.url, data={'value': 3})
        self.assertEqual(200, resp.status_code)
        resp_data = json.loads(resp.content)
        self.assertEqual(0, resp_data['status'])
        self.assertEqual(1, CourseStudentRating.objects.count())

    # 2.2.1
    def test_add_rating_lt_3_without_text(self):
        resp = self.client.post(self.url, data={'value': 2})
        self.assertEqual(200, resp.status_code)
        resp_data = json.loads(resp.content)
        self.assertNotEqual(0, resp_data['status'])
        self.assertEqual(0, CourseStudentRating.objects.count())

    # 2.2.2
    def test_add_rating_lt_3_text_len_10000(self):
        resp = self.client.post(self.url, data={'value': 2, 'text': 'q' * 100000})
        self.assertEqual(200, resp.status_code)
        resp_data = json.loads(resp.content)
        self.assertNotEqual(0, resp_data['status'])
        self.assertEqual(0, CourseStudentRating.objects.count())

    # 2.2.3
    def test_add_rating_lt_3_text_len_1000(self):
        resp = self.client.post(self.url, data={'value': 2, 'text': 'q' * 1000})
        self.assertEqual(200, resp.status_code)
        resp_data = json.loads(resp.content)
        self.assertEqual(0, resp_data['status'])
        self.assertEqual(1, CourseStudentRating.objects.count())

    # 2.2.4
    def test_add_rating_lt_3_text_len_100(self):
        resp = self.client.post(self.url, data={'value': 2, 'text': 'q' * 100})
        self.assertEqual(200, resp.status_code)
        resp_data = json.loads(resp.content)
        self.assertNotEqual(0, resp_data['status'])
        self.assertEqual(0, CourseStudentRating.objects.count())

    # 2.3
    def test_add_declined_rating(self):
        csr = CourseStudentRating.objects.create(user=self.user, session=self.session, rating=3, declined=True)
        resp = self.client.post(self.url, data={'value': 4})
        self.assertEqual(200, resp.status_code)
        resp_data = json.loads(resp.content)
        self.assertNotEqual(0, resp_data['status'])
        self.assertEqual(1, CourseStudentRating.objects.count())
        self.assertEqual(CourseStudentRating.objects.first().rating, csr.rating)

    # 2.4
    def test_incorrect_rating_input_doesnt_change_mean_rating(self):
        resp = self.client.post(self.url, data={'value': 4})
        self.assertEqual(200, resp.status_code)
        resp_data = json.loads(resp.content)
        self.assertEqual(0, resp_data['status'])
        self.assertEqual(1, CourseStudentRating.objects.count())
        self.session.refresh_from_db()
        self.assertEqual(4, self.session.course_rating)
        self.course.refresh_from_db()
        self.assertEqual(4, self.course.course_rating)

        resp = self.client.post(self.url, data={'value': 2})
        self.assertEqual(200, resp.status_code)
        resp_data = json.loads(resp.content)
        self.assertNotEqual(0, resp_data['status'])
        self.assertEqual(1, CourseStudentRating.objects.count())
        self.session.refresh_from_db()
        self.assertEqual(4, self.session.course_rating)
        self.course.refresh_from_db()
        self.assertEqual(4, self.course.course_rating)

    # 2.5
    def test_correct_rating_update_changes_mean_rating(self):
        resp = self.client.post(self.url, data={'value': 4})
        self.assertEqual(200, resp.status_code)
        resp_data = json.loads(resp.content)
        self.assertEqual(0, resp_data['status'])
        self.assertEqual(1, CourseStudentRating.objects.count())
        self.session.refresh_from_db()
        self.assertEqual(4, self.session.course_rating)
        self.course.refresh_from_db()
        self.assertEqual(4, self.course.course_rating)

        resp = self.client.post(self.url, data={'value': 5})
        self.assertEqual(200, resp.status_code)
        resp_data = json.loads(resp.content)
        self.assertEqual(0, resp_data['status'])
        self.assertEqual(1, CourseStudentRating.objects.count())
        self.session.refresh_from_db()
        self.assertEqual(5, self.session.course_rating)
        self.course.refresh_from_db()
        self.assertEqual(5, self.course.course_rating)
