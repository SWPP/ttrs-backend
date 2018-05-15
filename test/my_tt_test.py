
def my_tt_test(uid, upwd):
    auth = (uid, upwd)
    base = 'http://localhost:8000/ttrs/my-time-tables/'

    import requests, json
    from ttrs.models import Lecture, Student, MyTimeTable

    print('\ntesting '+'\033[1m'+base+'\033[0m...')
    data = {}
    data['title'] = 'my timetable'
    data['memo'] = 'memo for tt'
    data['lectures'] = [Lecture.objects.all()[0].id]
    
    res = requests.post(base, auth=auth, data=data)
    if res.status_code == 201:
        print('Successfully created my time table instance.')
    else:
        print('Error creating my time table instance.')
        print(res.text)
        return False

    res = requests.get(base, auth=auth)
    if res.status_code == 200:
        print('Successfully accessed my time table list.')
    else:
        print('Error accessing my time table list.')
        return False

    stu = Student.objects.filter(username=uid)[0]
    detail = base+str(MyTimeTable.objects.filter(owner=stu)[0].id)+'/'
    print('\ntesting \033[1m'+detail+'\033[0m...')
    res = requests.get(detail, auth=auth)
    if res.status_code == 200:
        print('Successfully accessed my time table detail.')
    else:
        print('Error accessing my time table detail.')
        return False

    data['title'] = 'my timetable is awesome!'
    res = requests.put(detail, auth=auth, data=data)
    if res.status_code == 200:
        print('Successfully modified my time table detail.')
    else:
        print('Error modifying my time table detail.')
        return False

    res = requests.delete(detail, auth=auth)
    if res.status_code == 204:
        print('Successfully deleted my time table detail.')
    else:
        print('Error deleting my time table detail.')
        return False

    return True
