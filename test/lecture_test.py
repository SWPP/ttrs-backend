
def lecture_test(uid, upwd):
    auth = (uid, upwd)
    base = 'http://localhost:8000/ttrs/lectures/'

    import json, requests

    print('\ntesting '+'\033[1m'+base+'\033[0m'+'...')
    res = requests.get(base, auth=auth)
    if res.status_code == 200:
        print('Successfully accessed Lecture list.')
    else:
        print('Error accessing Lecture list.')
        return False


    from ttrs.models import Lecture
    lecture = Lecture.objects.all()[0]

    filter = base+'?id='+str(lecture.id)
    print('\ntesting '+'\033[1m'+filter+'\033[0m'+'...')
    res = requests.get(filter, auth=auth)
    if res.status_code == 200:
        print('Successfully accessed Lecture list with payload.')
    else:
        print('Error accessing Lecture list with keyword.')
        return False

    filter = base+'?instructor__contains='+str(lecture.instructor)
    print('\ntesting '+'\033[1m'+filter+'\033[0m'+'...')
    res = requests.get(filter, auth=auth)
    if res.status_code == 200:
        print('Successfully accessed Lecture list with payload.')
    else:
        print('Error accessing Lecture list with keyword.')
        return False

    print('\n\033[1m'+'testing invalid data...'+'\033[0m')
    filter = base+'?asdf=asdf'
    res = requests.get(filter, auth=auth)
    print(filter, res)
    errors = json.loads(res.text)
    for error in errors:
        print(error, errors.get(error))

    detail = base+str(lecture.id)+'/'

    print('\ntesting '+'\033[1m'+detail+'\033[0m'+'...')
    res = requests.get(detail, auth=auth)
    if res.status_code == 200:
        print('Successfully accessed Lecture detail.')
    else:
        print('Error accessing Lecture detail.')
        return False

    return True


