
def evaluation_test(uid, upwd):
    auth = (uid, upwd)
    base = 'http://localhost:8000/ttrs/evaluations/'

    import json, requests
    from ttrs.models import Lecture, Evaluation

    print('\ntesting '+'\033[1m'+base+'\033[0m'+'...')
    for i in range(1,4):
        data = {}
        data['rate'] = 5
        data['comment'] = 'Wonderful lecture!'
        data['lecture'] = Lecture.objects.all()[i].id

        print('\nCreating Evaluation {}...'.format(i))
        res = requests.post(base, auth=auth, data=data)

        if res.status_code == 201:
            print('Successfully created Evaluation instance.')
            print(res.text)
        else:
            print('Error creating Evaluation instance.')
            print(res.text)

    print('\n'+'\033[1m'+'testing invalid data...'+'\033[0m')
    data = {}
    data['rate'] = 99
    data['comment'] = ''
    data['lecture'] = 0

    res = requests.post(base, auth=auth, data=data)
    print(res)
    errors = json.loads(res.text)
    for error in errors:
        print(error, errors.get(error))

    print('\ntesting '+'\033[1m'+base+'\033[0m')
    res = requests.get(base, auth=auth)
    if res.status_code == 200:
        print('Successfully accessed Evaluation list.')
    else:
        print('Error accessing Evaluation list.')
        print(res.content)
        return False

    filter = base+'?id='+str(Lecture.objects.all()[0].id)
    print('\ntesting '+'\033[1m'+filter+'\033[0m')
    res = requests.get(filter, auth=auth)
    if res.status_code == 200:
        print('Successfully accessed Evaluation list with payload.')
    else:
        print('Error accessing Evaluation list with payload.')
        print(res.content)
        return False

    filter = base+'?lecture__course__name__contains=글'
    print('\ntesting '+'\033[1m'+filter+'\033[0m')
    res = requests.get(filter, auth=auth)
    if res.status_code == 200:
        print('Successfully accessed Evaluation list with payload.')
    else:
        print('Error accessing Evaluation list with payload.')
        print(res.content)
        return False
    
    detail = base+str(Evaluation.objects.all()[0].id)+'/'
    print('\ntesting '+'\033[1m'+detail+'\033[0m')
    res = requests.get(detail, auth=auth)
    if res.status_code == 200:
        print('Successfully accessed Evaluation detail.')
    else:
        print('Error accessing Evaluation detail.')
        print(res.content)
        return False

    return True
