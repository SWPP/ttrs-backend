from django.contrib.auth.models import User
from django.test import TestCase, Client

import time

class TablesViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.my_admin = User.objects.create_superuser('superuser', '', 'qwertyasdf')

    def signIn(self, username, password):
        self.assertTrue(self.client.login(username=username, password=password))

    def test_retrieve(self):
        self.signIn('superuser', 'qwertyasdf')
        response = self.client.get('/manager/tables/')
        self.assertEqual(response.status_code, 200)

    def test_create(self):
        self.signIn('superuser', 'qwertyasdf')
        self.client.post('/manager/tables/', {})
        self.client.post('/manager/tables/', {'tables': ['MyTimeTable']})


class CrawlerViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.my_admin = User.objects.create_superuser('superuser', '', 'qwertyasdf')
        print(User.objects.all())

    def signIn(self, username, password):
        self.assertTrue(self.client.login(username=username, password=password))

    def test_crawler(self):
        self.signIn('superuser', 'qwertyasdf')
        self.client.get('manager/crawlers/')
        #self.client.post('/manager/crawlers/', {'year': 2018, 'semester': '1학기'})
        #time.sleep(30)
        #self.client.put('/manager/crawlers/1')