
def course_test(uid, upwd):
    auth = (uid, upwd)
    base = 'http://localhost:8000/ttrs/courses/'

    import json, requests

    print('\ntesting '+'\033[1m'+base+'\033[0m'+'...')
    res = requests.get(base, auth=auth)
    if res.status_code == 200:
        print('Successfully accessed Course list.')
    else:
        print('Error accessing Course list.')
        return False

    from ttrs.models import Course
    course = Course.objects.all()[0]

    filter = base+'?id='+str(course.id)
    print('\ntesting '+ '\033[1m'+filter+'\033[0m...')
    res = requests.get(filter, auth=auth)
    if res.status_code == 200:
        print('Successfully accessed Course list with payload.')
    else:
        print('Error accessing Course list with payload.')
        return False

    filter = base+'?type=교양'
    print('\ntesting \033[1m'+filter+'\033[0m...')
    res = requests.get(filter, auth=auth)
    if res.status_code == 200:
        print('Successfully accessed Course list with payload.')
    else:
        print('Error accessing Course list with payload.')
        return False

    print('\n\033[1m'+'testing invalid data...'+'\033[0m')
    filter = base+'?asdf=asdf'
    res = requests.get(filter, auth=auth)
    print(filter, res)
    errors = json.loads(res.text)
    for error in errors:
        print(error, errors.get(error))

    detail = base+str(course.id)+'/'
    print('\ntesting '+'\033[1m'+detail+'\033[0m'+'...')
    res = requests.get(detail, auth=auth)
    if res.status_code == 200:
        print('Successfully accessed Course detail.')
    else:
        print('Error accessing Course detail.')
        return False

    return True
