
def student_test(uid, upwd):
    auth = (uid, upwd)
    base = 'http://localhost:8000/ttrs/students/'
    signup = base+'signup/'
    my = base+'my/'
    
    import json
    import requests

    # Test if objects are created with valid data.
    print('\ntesting '+'\033[1m'+signup+'\033[0m'+'...')
    for i in range(1,4):
        data = {}
        data['username'] = 'stu{}'.format(i)
        data['password'] = 'qwertyasdf'
        data['email'] = 'stu{}@snu.ac.kr'.format(i)
        data['grade'] = 1

        from ttrs.models import College
        data['college'] = College.objects.all()[0].id

        print('\nCreating student {}...'.format(i))
        res = requests.post(signup, data=data)

        if res.status_code == 201:
            print('Successfully created Student instance.')
            #print(res.text)
        else:
            print('Error creating Student instance.')
            print(res.text)
            return False

    # Test if view correctly handles invalid data.
    data = {}
    data['username'] = 'stu1'
    data['password'] = '1234'
    data['email'] = 'stu@google.com'
    data['grade'] = 10
    data['college'] = 0

    print('\n'+'\033[1m'+'testing invalid data...'+'\033[0m')
    res = requests.post(signup, data=data)
    errors = json.loads(res.text)
    for error in errors:
        print(error, errors.get(error))

    
    print('\n'+'testing '+'\033[1m'+base+'\033[0m'+'...')
    res = requests.get(base, auth=auth)
    if res.status_code == 200:
        print('Successfully accessed Student list.')
        #print(res.text)
    else:
        print('Error accessing Student list.')
        print(res.text)
        return False

    return True
