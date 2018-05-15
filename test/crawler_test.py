import requests
import time

def crawler_test(uid, upwd):
    auth = (uid, upwd)
    base = 'http://localhost:8000/manager/crawlers/'
    data = {'year':'2018', 'semester':'1학기'}

    import requests
    print('\n'+'testing '+'\033[1m'+base+'\033[0m'+'...')
    print('Creating crawler', data, '...')
    res = requests.post(base, auth=auth, data=data)
    if res.status_code == 201:
        print('Successfully created Crawler instance.')

        import json
        cid = json.loads(res.text)['id']
        print('Running Crawler {}...'.format(cid))

        import time
        time.sleep(30)

        detail = base+str(cid)+'/'
        print('\n'+'testing '+'\033[1m'+detail+'\033[0m'+'...')
        print('Stopping Crawler instance...')
        if requests.put(detail, auth=auth).status_code == 200:
            print('Successfully stopped Crawler instance.')
        else:
            print('Error stopping Crawler instance.')
            return False

    else:
        print('Error creating Crawler instance.')
        return False

    return True

