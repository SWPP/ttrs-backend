
def re_tt_test(uid, upwd):
    auth = (uid, upwd)
    base = 'http://localhost:8000/ttrs/received-time-tables/'

    import requests, json
    from ttrs.models import Student, ReceivedTimeTable

    stu = Student.objects.filter(username=uid)[0]
    tt = ReceivedTimeTable.objects.filter(owner=stu)[0]

    print('\ntesting \033[1m'+base+'\033[0m...')
    res = requests.get(base, auth=auth)
    if res.status_code == 200:
        print('Successfully accessed received time table list.')
    else:
        print('Error accessing received time table list.')
        return False

    detail = base+str(tt.id)+'/'
    print('\ntesting \033[1m'+detail+'\033[0m...')
    res = requests.get(detail, auth=auth)
    if res.status_code == 200:
        print('Successfully accessed received time table detail.')
    else:
        print('Error accessing received time table detail.')

    receive = detail+'receive/'
    print('\ntesting \033[1m'+receive+'\033[0m...')
    res = requests.get(base, auth=auth)
    if res.status_code == 200:
        print('Successfully received a time table.')
    else:
        print('Error receiving a time table.')

    return True
