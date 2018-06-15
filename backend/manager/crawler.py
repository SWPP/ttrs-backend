"""
function run is called by view with argument crawler.
while crawling the site, it updates status of the crawler and
checks cancel_flag of it.
If cancel_flag is True, it stops current job and set status to 'canceled'.
"""

import os, time
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from ttrs.models import *

driver_path = os.path.join(settings.BASE_DIR, '../chromedriver')

sid = {'1학기': 1,
       '2학기': 2,
       '여름학기': 3,
       '겨울학기': 4
}

total_cnt = 0           # total number of lectures
total_fin = 0           # number of lectures finished
total_page = 0          # total number of pages
total_page_fin = 0      # number of finished pages
detail = ''             # detail for crawler status


def update(crawler, status, detail):
    crawler.refresh_from_db()
    if crawler.cancel_flag:
        crawler.status = 'canceled: '+detail
        crawler.save()
        return False

    else:
        crawler.status = status+': '+detail
        crawler.save()
        return True


def run(crawler):
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument('disable-gpu')
        options.add_argument('User-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KTHML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')

        driver = webdriver.Chrome(driver_path, chrome_options=options)
        time.sleep(2)

        driver.get('https://sugang.snu.ac.kr/sugang/cc/cc100.action')
        time.sleep(1)
        # detailed search
        driver.find_element_by_id('detail_button').click()
        time.sleep(2)
        # select year
        driver.execute_script("document.getElementById('srchOpenSchyy').value = '{}'".format(crawler.year))
        time.sleep(1)
        # select semester
        driver.find_element_by_xpath('//*[@id="srchOpenShtm"]/option[{}]'.format(sid[crawler.semester])).click()
        time.sleep(1)
        # select bachelor's course
        driver.find_element_by_xpath('//*[@id="srchOpenSubmattCorsFg"]/option[2]').click()
        time.sleep(1)

        # clicks search button
        driver.find_element_by_class_name('btn_search_ok').click()
        
        global total_cnt
        global total_fin
        global total_page
        global detail

        total_cnt = int(driver.find_element_by_xpath('//*[@id="content"]/div/div[3]/div[1]/div[1]/h3/span').text)
        total_fin = 0
        total_page = ((total_cnt-1)//10)+1
        total_page_fin = 0
        detail = ''

        type_select = driver.find_element_by_xpath('//*[@id="srchOpenSubmattFgCd"]')
        types = [x.text.strip() for x in type_select.find_elements_by_tag_name('option')]
        type_cnt = len(types)

        print(types, type_cnt)
        for t in range(2, type_cnt+1):
            if update(crawler, 'running', detail):
                print('start running ', types[t-1])
                crawl_type(crawler, driver, t, types[t-1])
            else:
                return

        crawler.status = 'finished {} lectures'.format(total_fin)
        crawler.save()

        driver.close()

    except NoSuchElementException as e:
        print(e)
        crawler.status = str('finished {} lectures due to error'.format(total_fin))
        crawler.save()

    except Exception as e:
        print('here!', e)
        crawler.status = str(e)
        crawler.save()


def crawl_type(crawler, driver, tid, type):
    # clears field and area
    driver.find_element_by_xpath('//*[@id="srchOpenUpSbjtFldCd"]/option[1]').click()
    driver.find_element_by_xpath('//*[@id="cond02"]/td[3]/select[2]/option[1]').click()

    # selects type
    driver.find_element_by_xpath('//*[@id="srchOpenSubmattFgCd"]/option[{}]'.format(tid)).click()
    driver.implicitly_wait(1)

    global total_cnt
    global total_fin
    global total_page
    global total_page_fin
    global detail

    if type != '교양':
        driver.find_element_by_class_name('btn_search_ok').click()
        driver.implicitly_wait(1)

        section_cnt = int(driver.find_element_by_xpath('//*[@id="content"]/div/div[3]/div[1]/div[1]/h3/span').text)
        section_page = ((section_cnt-1)//10)+1

        print('starting {}...'.format(type))
        for i in range(1, section_page+1):
            detail = '{} page {}/{} total {}/{} lectures'.format(type, i, section_page, total_fin, total_cnt)
            if update(crawler, 'running', detail) is False:
                print(type, crawler.status, crawler.cancel_flag)
                return

            # goes to page i
            driver.execute_script('fnGotoPage({})'.format(i))
            # crawls a table of lectures in current page
            print('='*20+'{} page {}/{}'.format(type, i, section_page)+'='*20)
            lectures = crawl(driver)
            # parses given data and saves it in DB
            parse(crawler.year, crawler.semester, lectures, '')

            total_fin += len(lectures)
            total_page_fin += 1

        print('='*20+'finished {}'.format(type)+'='*20)

    else: # type == '교양'
        field_select = driver.find_element_by_xpath('//*[@id="srchOpenUpSbjtFldCd"]')
        fields = [x.text.strip() for x in field_select.find_elements_by_tag_name('option')]
        field_cnt = len(fields)

        for i in range(2, field_cnt+1):
            field = fields[i-1]
            driver.find_element_by_xpath('//*[@id="srchOpenUpSbjtFldCd"]/option[{}]'.format(i)).click()

            area_select = driver.find_element_by_xpath('//*[@id="cond02"]/td[3]/select[2]')
            areas = [x.text.strip() for x in area_select.find_elements_by_tag_name('option')]
            area_cnt = len(areas)

            for j in range(2, area_cnt+1):
                area = areas[j-1]
                driver.find_element_by_xpath('//*[@id="cond02"]/td[3]/select[2]/option[{}]'.format(j)).click()
                time.sleep(1)

                driver.find_element_by_class_name('btn_search_ok').click()
                driver.implicitly_wait(1)

                section_cnt = int(driver.find_element_by_xpath('//*[@id="content"]/div/div[3]/div[1]/div[1]/h3/span').text)
                section_page = ((section_cnt - 1) // 10) + 1

                for p in range(1, section_page+1):
                    detail = '{} ({}-{}) {}/{} total {}/{} lectures'.format(type, field, area, p, section_page, total_fin, total_cnt)
                    if update(crawler, 'running', detail) is False:
                        return

                    # goes to page p
                    driver.execute_script('fnGotoPage({})'.format(p))
                    # crawls a table of lectures in current page
                    print('='*20+'{} ({}-{}) page {}/{}'.format(type, field, area, p, section_page)+'='*20)
                    lectures = crawl(driver)
                    # parses given data and saves it in DB
                    parse(crawler.year, crawler.semester, lectures, field + '-' + area)
                    # increments number of lectures and pages finished
                    total_fin += len(lectures)
                    total_page_fin += 1

                print('='*20+'finished {} ({}-{})'.format(type, field, area)+'='*20)


def crawl(driver):
    lectures = []
    errors = []

    # 'elts' is a table of lectures displayed in current page
    elts = driver.find_element_by_xpath('//*[@id="content"]/div/div[3]/div[1]/div[2]/table/tbody')
    lecture = None
    for row in elts.find_elements_by_tag_name('tr'):
        try:
            columns = row.find_elements_by_tag_name('td')

            if not columns[0].text:
                if lecture is not None:
                    lectures.append(lecture)

                department_major = columns[3].text
                if department_major != '':
                    if department_major[0] == '(':
                        department_major = department_major[1:]

                    if department_major[-1] == ')':
                        department_major = department_major[:-1]

                    index = department_major.find('(')
                    if index != -1:
                        department = department_major[:index]
                        major = department_major[index+1:]
                    else:
                        department = department_major
                        major = ''
                else:
                    department = ''
                    major = ''

                lecture = {
                    'type': columns[1].text,
                    'name': columns[8].text,
                    'college': columns[2].text,
                    'department': department,
                    'major': major,
                    'grade': columns[5].text,
                    'instructor': columns[13].text,
                    'code': columns[6].text,
                    'number': columns[7].text,
                    'credit': columns[9].text,
                    'note': columns[17].text,
                }

                if not columns[10].text:
                    raise Exception('No time slot')

                classroom = columns[12].text.split('-')
                if len(classroom) == 3:
                    if len(classroom[1]) == 1:
                        building = classroom[0] + '-' + classroom[1]
                        room_no = classroom[2]
                    else:
                        building = classroom[0]
                        room_no = classroom[1] + '-' + classroom[2]

                elif len(classroom) == 2:
                    building = classroom[0]
                    room_no = classroom[1]

                else:
                    building = classroom[0]
                    room_no = ''

                time_slot = {
                    'time': columns[10].text,
                    'classroom': {
                        'building': building,
                        'room_no': room_no,
                    }
                }

                lecture['time_slots'] = [time_slot]

            else:
                if not columns[0].text:
                    raise Exception('No time slot')

                classroom = columns[2].text.split('-')
                if len(classroom) == 3:
                    if len(classroom[1]) == 1:
                        building = classroom[0] + '-' + classroom[1]
                        room_no = classroom[2]
                    else:
                        building = classroom[0]
                        room_no = classroom[1] + '-' + classroom[2]

                elif len(classroom) == 2:
                    building = classroom[0]
                    room_no = classroom[1]

                else:
                    building = classroom[0]
                    room_no = ''

                time_slot = {
                    'time': columns[0].text,
                    'classroom': {
                        'building': building,
                        'room_no': room_no,
                    }
                }

                lecture['time_slots'].append(time_slot)

        except Exception as e:
            errors.append(str(e))

    if lecture is not None:
        lectures.append(lecture)

    return lectures


def parse(year, semester, lectures, field_name):
    for lecture in lectures:
        try:
            college_instance = College.objects.get(name=lecture['college'])
        except ObjectDoesNotExist:
            college_instance = College.objects.create(name=lecture['college'])
            college_instance.save()

        try:
            department_instance = Department.objects.get(name=lecture['department'])
        except ObjectDoesNotExist:
            if lecture['department'] != '':
                department_instance = Department.objects.create(college=college_instance,
                                                            name=lecture['department'])
                department_instance.save()

            else:
                department_instance = None

        try:
            major_instance = Major.objects.get(name=lecture['major'])
        except ObjectDoesNotExist:
            if lecture['major'] != '':
                major_instance = Major.objects.create(department=department_instance,
                                                  name=lecture['major'])
                major_instance.save()

            else:
                major_instance = None

        try:
            course_instance = Course.objects.get(code=lecture['code'])

        except ObjectDoesNotExist:
            course_instance = Course.objects.create(code=lecture['code'],
                                                    name=lecture['name'],
                                                    type=lecture['type'],
                                                    field=field_name,
                                                    grade=int(lecture['grade'][0]) if len(lecture['grade']) else 0,
                                                    credit=int(lecture['credit'].split('-')[0]),
                                                    college=college_instance,
                                                    department=department_instance,
                                                    major=major_instance,
                                                    )
            course_instance.save()

        try:
            lecture_instance = Lecture.objects.create(course=course_instance,
                                                      year=year,
                                                      semester=semester,
                                                      number=lecture['number'],
                                                      instructor=lecture['instructor'],
                                                      note=lecture['note'])
        except Exception as e:
            print('The lecture instance already exists')
            continue

        # It really is absurd, but there exists lectures without any time slot.
        try:
            for time_slot in lecture['time_slots']:
                building = time_slot['classroom']['building']
                room_no = time_slot['classroom']['room_no']

                try:
                    classroom_instance = Classroom.objects.get(building=building, room_no=room_no)
                except ObjectDoesNotExist:
                    if building != '' or room_no != '':
                        classroom_instance = Classroom.objects.create(building=building,
                                                                      room_no=room_no)
                        classroom_instance.save()
                    else:
                        classroom_instance = None

                timeslot_instance = TimeSlot.objects.create(day_of_week=time_slot['time'][0],
                                                            start_time=time_slot['time'][2:7],
                                                            end_time=time_slot['time'][8:13],
                                                            classroom=classroom_instance)
                timeslot_instance.save()
                lecture_instance.time_slots.add(timeslot_instance)

        except Exception as e:
            print('parse', e)


        print('course:', lecture['name'], 'type:', lecture['type'], 'field:', field_name)
