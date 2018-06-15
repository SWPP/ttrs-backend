import json

from django.contrib.auth.hashers import make_password
from django.test import TestCase, Client

from .models import College, Student, Department, Major, Course, Lecture, TimeSlot, Evaluation, MyTimeTable


class BaseTestCase(TestCase):
    def setUp(self):
        # This comment is for crawling setUp.
        # I leave this implementation for the case that we must use crawled data
        #
        # admin = User(username='user', is_staff=True)
        # admin.set_password('password')
        # admin.save()
        # client = Client()
        # client.login(username='user', password='password')
        #
        # response = client.post('/manager/crawlers/', data={
        #     'year': 2018,
        #     'semester': '1학기',
        # })
        # crawler_id = response.json()['id']
        #
        # from time import sleep
        # for i in range(30):
        #     response = client.get('/manager/crawlers/{}/'.format(crawler_id))
        #     sleep(1)
        # assert 'running' in response.json()['status']
        #
        # client.put('/manager/crawlers/{}/'.format(crawler_id))
        # for i in range(30):
        #     response = client.get('/manager/crawlers/{}/'.format(crawler_id))
        #     if 'running' not in response.json()['status']:
        #         break
        #     sleep(1)
        # assert 'canceled' in response.json()['status']

        college1 = College.objects.create(name='college1')
        department1 = Department.objects.create(name='department1', college=college1)
        major1 = Major.objects.create(name='major1', department=department1)
        college2 = College.objects.create(name='college2')
        department2 = Department.objects.create(name='department2', college=college2)
        college3 = College.objects.create(name='college3')

        course1 = Course.objects.create(name='course1', code='code1', type='전필', grade=3, credit=4, college=college1, department=department1)
        course2 = Course.objects.create(name='course2', code='code2', type='전선', grade=2, credit=3, college=college1, department=department1, major=major1)
        course3 = Course.objects.create(name='course3', code='code3', type='교양', grade=1, credit=2, college=college2, department=department2)

        time_slot1 = TimeSlot.objects.create(day_of_week='월', start_time='12:00', end_time='13:15')
        time_slot2 = TimeSlot.objects.create(day_of_week='수', start_time='12:00', end_time='13:15')
        time_slot3 = TimeSlot.objects.create(day_of_week='금', start_time='16:00', end_time='18:00')
        lecture = Lecture.objects.create(course=course1, year=2018, semester='1학기', number='001', instructor='가나다', note='')
        lecture.time_slots.add(time_slot1)
        lecture.time_slots.add(time_slot2)
        lecture.time_slots.add(time_slot3)

        time_slot1 = TimeSlot.objects.create(day_of_week='월', start_time='14:00', end_time='15:15')
        time_slot2 = TimeSlot.objects.create(day_of_week='수', start_time='14:00', end_time='15:15')
        time_slot3 = TimeSlot.objects.create(day_of_week='목', start_time='9:00', end_time='10:45')
        lecture = Lecture.objects.create(course=course1, year=2018, semester='1학기', number='002', instructor='ABC', note='RRR')
        lecture.time_slots.add(time_slot1)
        lecture.time_slots.add(time_slot2)
        lecture.time_slots.add(time_slot3)

        time_slot1 = TimeSlot.objects.create(day_of_week='월', start_time='12:00', end_time='13:15')
        time_slot2 = TimeSlot.objects.create(day_of_week='수', start_time='12:00', end_time='13:15')
        time_slot3 = TimeSlot.objects.create(day_of_week='금', start_time='16:00', end_time='18:00')
        lecture = Lecture.objects.create(course=course3, year=2018, semester='1학기', number='001', instructor='가나다', note='')
        lecture.time_slots.add(time_slot1)
        lecture.time_slots.add(time_slot2)
        lecture.time_slots.add(time_slot3)

        time_slot1 = TimeSlot.objects.create(day_of_week='월', start_time='12:00', end_time='13:15')
        time_slot2 = TimeSlot.objects.create(day_of_week='수', start_time='12:00', end_time='13:15')
        time_slot3 = TimeSlot.objects.create(day_of_week='금', start_time='16:00', end_time='18:00')
        lecture = Lecture.objects.create(course=course2, year=2018, semester='여름학기', number='001', instructor='가나다', note='')
        lecture.time_slots.add(time_slot1)
        lecture.time_slots.add(time_slot2)
        lecture.time_slots.add(time_slot3)

        data = {
            'username': 'stu1',
            'password': make_password('password'),
            'email': 'stu1@snu.ac.kr',
            'grade': 3,
            'college_id': 1,
            'department_id': 1,
        }
        self.student = Student.objects.create(**data)
        data = {
            'username': 'stu2',
            'password': make_password('password'),
            'email': 'stu2@snu.ac.kr',
            'grade': 3,
            'college_id': 1,
            'department_id': 1,
        }
        self.student2 = Student.objects.create(**data)
        data = {
            'username': 'stu3',
            'password': make_password('password'),
            'email': 'stu3@snu.ac.kr',
            'grade': 3,
            'college_id': 1,
            'department_id': 1,
        }
        self.student3 = Student.objects.create(**data)

        self.client = Client()
        self.sign_in()

    def sign_in(self, username='stu1'):
        self.assertTrue(self.client.login(username=username, password='password'))

    def get_test(self, url, success=True, status_code=None):
        response = self.client.get(url)
        print(response.json())
        self.assertEqual(response.status_code, status_code if status_code else 200 if success else 400)
        return response

    def post_test(self, url, data, success=True, status_code=None):
        response = self.client.post(url, data=data)
        print(response.json())
        self.assertEqual(response.status_code, status_code if status_code else 201 if success else 400)
        return response

    def put_test(self, url, data, success=True, status_code=None):
        response = self.client.put(url, data=json.dumps(data), content_type='application/json')
        print(response.json())
        self.assertEqual(response.status_code, status_code if status_code else 200 if success else 400)
        return response

    def patch_test(self, url, data, success=True, status_code=None):
        response = self.client.patch(url, data=json.dumps(data), content_type='application/json')
        print(response.json())
        self.assertEqual(response.status_code, status_code if status_code else 200 if success else 400)
        return response

    def delete_test(self, url, status_code=None):
        response = self.client.delete(url)
        print(response.status_code)
        self.assertEqual(response.status_code, status_code if status_code else 204)
        return response


class StudentViewTest(BaseTestCase):
    url_my = '/ttrs/students/my/'

    def test_sign_up(self):
        response = self.post_test('/ttrs/students/signup/', {
            'username': 'student',
            'password': 'paawsesfawword',
            'email': 'student@snu.ac.kr',
            'grade': 3,
            'college': 1,
            'department': 1,
        })

    def test_my_retrieve(self):
        response = self.get_test(self.url_my)

    def test_my_update_success(self):
        response = self.patch_test(self.url_my, dict(grade=1))
        self.assertEqual(response.json()['grade'], 1)

    def test_my_update_fail(self):
        errors = [
            dict(password='password'),
            dict(email='email'),
            dict(email='stu1@gmail.com'),
            dict(college=-1),
            dict(college=1, department=2),
            dict(college=1, department=1, major=2),
        ]
        for error_input in errors:
            response = self.patch_test(self.url_my, error_input, False)
            self.assertEqual(response.status_code, 400)

    def test_my_delete(self):
        response = self.delete_test(self.url_my)


class CourseViewTest(BaseTestCase):
    def test_list(self):
        response = self.get_test('/ttrs/courses/')
        response = self.get_test('/ttrs/courses/?order_by=credit')
        response = self.get_test('/ttrs/courses/?order_by=asdf')

    def test_retrieve(self):
        response = self.get_test('/ttrs/courses/1/')


class LectureViewTest(BaseTestCase):
    def test_list(self):
        response = self.get_test('/ttrs/lectures/')

    def test_retrieve(self):
        response = self.get_test('/ttrs/lectures/1/')
        response = self.get_test('/ttrs/lectures/192318/', status_code=404)

    def test_search(self):
        course = Course.objects.create(name='소프트웨어 개발의 원리와 실제', code='M231-313', type='전필', grade=3, credit=3, college_id=1)
        lecture = Lecture.objects.create(course=course, year=2018, semester='1학기', number='001', instructor='ㅎㅎㅎ')
        response = self.get_test('/ttrs/lectures/?course__name__abbrev=소개원실')
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['id'], lecture.id)
        self.assertEqual(response.json()[0]['course']['id'], course.id)


class EvaluationViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        e = Evaluation.objects.create(author=self.student, lecture_id=2, rate=8, comment='asdf')
        e.like_it.add(self.student2)
        e.like_it.add(self.student3)
        e.save()
        e = Evaluation.objects.create(author=self.student2, lecture_id=1, rate=3, comment='asdfsdfwef')
        e.like_it.add(self.student3)
        e.save()
        e = Evaluation.objects.create(author=self.student3, lecture_id=3, rate=4, comment='asdsdfsdfwef')
        e.like_it.add(self.student)
        e.like_it.add(self.student2)
        e.save()

    def test_list(self):
        response = self.get_test('/ttrs/evaluations/')
        self.assertEqual(len(response.json()), 3)

    def test_create(self):
        response = self.post_test('/ttrs/evaluations/', dict(
            lecture=1,
            rate=10,
            comment='asdf',
        ))

    def test_retrieve(self):
        response = self.get_test('/ttrs/evaluations/2/')

    def test_partial_update_fail(self):
        errors = [
            dict(rate=-1),
            dict(rate=11),
        ]
        for error in errors:
            response = self.patch_test('/ttrs/evaluations/1/', error, False)
        response = self.patch_test('/ttrs/evaluations/2/', {}, status_code=403)

    def test_destroy(self):
        response = self.get_test('/ttrs/evaluations/1/')

    def test_like_it(self):
        response = self.get_test('/ttrs/evaluations/2/likeit/')
        self.assertEqual(len(response.json()['like_it']), 2)

    def test_like_it_cancel(self):
        response = self.delete_test('/ttrs/evaluations/3/likeit/', status_code=200)
        self.assertEqual(len(response.json()['like_it']), 1)

    def test_like_it_fail(self):
        response = self.get_test('/ttrs/evaluations/1/likeit/', status_code=403)


class SemesterViewTest(BaseTestCase):
    def test_list(self):
        response = self.get_test('/ttrs/semesters/')


class CollegeViewTest(BaseTestCase):
    def test_list(self):
        response = self.get_test('/ttrs/colleges/')


class MyTimeTableViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()

        response = self.post_test('/ttrs/my-time-tables/', dict(
            title='table1',
            lectures=[2, 3],
        ))
        response = self.post_test('/ttrs/bookmarked-time-tables/', dict(
            title='table2',
            lectures=[4],
        ))

    def test_create(self):
        response = self.post_test('/ttrs/my-time-tables/', dict(
            title='new table',
            lectures=[2, 3],
        ))
        response = self.get_test('/ttrs/my-time-tables/1/', status_code=404)

    def test_create2(self):
        response = self.post_test('/ttrs/my-time-tables/', dict(
            title='new table',
            lectures=[4]
        ))
        response = self.get_test('/ttrs/my-time-tables/1/')

    def test_create_fail(self):
        response = self.post_test('/ttrs/my-time-tables/', dict(
            title='table1',
            lectures=[1, 2],
        ), False)
        response = self.post_test('/ttrs/my-time-tables/', dict(
            title='table1',
            lectures=[1, 3],
        ), False)

    def test_list(self):
        response = self.get_test('/ttrs/my-time-tables/')
        self.assertEqual(len(response.json()), 1)

    def test_retrieve(self):
        response = self.get_test('/ttrs/my-time-tables/1/')

    def test_partial_update(self):
        response = self.patch_test('/ttrs/my-time-tables/1/', dict(
            lectures=[1, 3],
        ), False)
        response = self.patch_test('/ttrs/my-time-tables/1/', dict(
            title=None,
        ), False)

    def test_destroy(self):
        response = self.delete_test('/ttrs/my-time-tables/1/')

    def test_copy_to_my(self):
        response = self.post_test('/ttrs/time-tables/copy-to-my/', dict(
            time_table_id=2
        ))
        response = self.get_test('/ttrs/my-time-tables/3/')
        self.assertEqual(response.json()['title'], 'table2')


class BookmarkTimeTableViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()

        response = self.post_test('/ttrs/bookmarked-time-tables/', dict(
            title='table1',
            lectures=[2, 3],
        ))
        response = self.post_test('/ttrs/my-time-tables/', dict(
            title='table2',
            lectures=[2, 3],
        ))

    def test_create_fail(self):
        response = self.post_test('/ttrs/bookmarked-time-tables/', dict(
            title='table1',
            lectures=[1, 2],
        ), False)
        response = self.post_test('/ttrs/bookmarked-time-tables/', dict(
            title='table1',
            lectures=[1, 3],
        ), False)

    def test_list(self):
        response = self.get_test('/ttrs/bookmarked-time-tables/')
        self.assertEqual(len(response.json()), 1)

    def test_retrieve(self):
        response = self.get_test('/ttrs/bookmarked-time-tables/1/')

    def test_partial_update(self):
        response = self.patch_test('/ttrs/bookmarked-time-tables/1/', dict(
            lectures=[1, 3],
        ), False)
        response = self.patch_test('/ttrs/bookmarked-time-tables/1/', dict(
            title=None,
        ), False)

    def test_destroy(self):
        response = self.delete_test('/ttrs/bookmarked-time-tables/1/')

    def test_bookmark(self):
        response = self.post_test('/ttrs/time-tables/bookmark/', dict(
            time_table_id=2,
        ))
        response = self.get_test('/ttrs/bookmarked-time-tables/3/')
        self.assertEqual(response.json()['title'], 'table2')


class ReceivedTimeTableViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.sign_in('stu2')
        response = self.post_test('/ttrs/my-time-tables/', dict(
            title='table1',
            lectures=[2, 3],
        ))
        response = self.post_test('/ttrs/bookmarked-time-tables/', dict(
            title='table2',
            lectures=[4],
        ))
        response = self.post_test('/ttrs/time-tables/send/', dict(
            receiver_name='stu1',
            time_table_id=1,
        ))
        self.sign_in()

    def test_list(self):
        response = self.get_test('/ttrs/received-time-tables/')
        self.assertEqual(len(response.json()), 1)
        self.assertIsNone(response.json()[0]['received_at'])

    def test_send_fail(self):
        response = self.post_test('/ttrs/time-tables/send/', dict(
            receiver_name='stu10239120391',
            time_table_id=3,
        ), False)

    def test_send_fail2(self):
        response = self.post_test('/ttrs/time-tables/send/', dict(
            receiver_name='stu2',
            time_table_id=1,
        ), False)

    def test_retrieve(self):
        response = self.get_test('/ttrs/received-time-tables/3/')
        self.assertEqual(response.json()['title'], 'table1')
        self.assertEqual(response.json()['sender'], self.student2.username)

    def test_destroy(self):
        response = self.delete_test('/ttrs/received-time-tables/3/')

    def test_receive(self):
        response = self.get_test('/ttrs/received-time-tables/3/receive/')
        self.assertIsNotNone(response.json()['received_at'])


class RecommendViewTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        # self.sign_in()

    def test_retrieve(self):
        response = self.get_test('/ttrs/recommends/')
        response = self.get_test('/ttrs/recommends/?year=2018&semester=1학기')
        response = self.get_test('/ttrs/recommends/?year=2017&semester=1학기&expected_credit=3')

class StaticViewTest(BaseTestCase):
    def test_retrieve(self):
        response = self.get_test('/ttrs/static-information/')
        response = self.get_test('/ttrs/static-information/?year=2018&semester=1학기')
