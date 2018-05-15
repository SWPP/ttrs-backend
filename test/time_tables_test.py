
def time_tables_test(uid, upwd):
    auth = (uid, upwd)
    base = 'http://localhost:8000/ttrs/time-tables/'

    bookmark = base+'bookmark/'
    send = base+'send/'
    copy_to_my = base+'copy-to-my/'

    import requests, json
    from ttrs.models import Student, Lecture, MyTimeTable

    data = {}
    data['title'] = 'test tt'
    data['memo'] = 'test memo'
    data['lectures'] = [Lecture.objects.all()[0].id]
    res = requests.post('http://localhost:8000/ttrs/my-time-tables/', auth=auth, data=data)

    stu = Student.objects.filter(username=uid)[0]
    tt = MyTimeTable.objects.filter(owner=stu)[0]
    print('\ntesting \033[1m'+bookmark+'\033[0m...')
    res = requests.post(bookmark, auth=auth, data={'time_table_id':tt.id})
    if res.status_code == 201:
        print('Successfully bookmarked a time table.')
    else:
        print('Error bookmarking a time table.')
        return False

    print('\ntesting \033[1m'+send+'\033[0m...')
    res = requests.post(send, auth=auth, data={'time_table_id':tt.id, 'receiver_name':'stu2'})
    if res.status_code == 201:
        print('Successfully sent a time table.')
    else:
        print('Error sending a time table.')
        return False

    print('\ntesting \033[1m'+copy_to_my+'\033[0m...')
    res = requests.post(copy_to_my, auth=auth, data={'time_table_id':tt.id})
    if res.status_code == 201:
        print('Successfully copied a time table to my time table.')
    else:
        print('Error copying a time table.')
        return False

    return True
