import os, sys
from django.conf import settings

test_path = os.path.join(settings.BASE_DIR, '../test/')
sys.path.append(test_path)

from crawler_test import crawler_test
from student_test import student_test
from course_test import course_test
from lecture_test import lecture_test
from evaluation_test import evaluation_test
from my_tt_test import my_tt_test
from bm_tt_test import bm_tt_test
from time_tables_test import time_tables_test
from re_tt_test import re_tt_test

uid = 'lame'
upwd = 'qwertyasdf'

print('\n'+'\033[1m'+'='*15, 'Crawler Test', '='*15+'\033[0m')
crawler = crawler_test(uid, upwd)

print('\n'+'\033[1m'+'='*15, 'Student Test', '='*15+'\033[0m')
student = student_test(uid, upwd)

print('\n'+'\033[1m'+'='*15, 'Course Test', '='*15+'\033[0m')
course = course_test(uid, upwd)

print('\n'+'\033[1m'+'='*15, 'Lecture Test', '='*15+'\033[0m')
lecture = lecture_test(uid, upwd)

print('\n'+'\033[1m'+'='*15, 'Evaluation Test', '='*15+'\033[0m')
evaluation = evaluation_test('stu1', 'qwertyasdf')

print('\n'+'\033[1m'+'='*15, 'My TT Test', '='*15+'\033[0m')
my_tt = my_tt_test('stu1', 'qwertyasdf')

print('\n'+'\033[1m'+'='*15, 'Bookmarked TT Test', '='*15+'\033[0m')
bm_tt = bm_tt_test('stu1', 'qwertyasdf')

print('\n'+'\033[1m'+'='*15, 'Time Tables Test', '='*15+'\033[0m')
tts = time_tables_test('stu1', 'qwertyasdf')

print('\n'+'\033[1m'+'='*15, 'Received TT Test', '='*15+'\033[0m')
re_tt = re_tt_test('stu2', 'qwertyasdf')


print('\n'+'\033[1m'+'='*15, 'Overall', '='*15+'\033[0m')
print('Crawler Test:', crawler)
print('Student Test:', student)
print('Course Test:', course)
print('Lecture Test:', lecture)
print('Evaluation Test:', evaluation)
print('My TT Test:', my_tt)
print('Bookmarked TT Test:', bm_tt)
print('Received TT Test:', re_tt)
print('Time Tables Test:', tts)
