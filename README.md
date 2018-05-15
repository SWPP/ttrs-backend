# ttrs-backend

## Initial Setting
### virtual environment
```console
$ virtualenv -p python3 venv
$ source venv/bin/activate
$ sudo apt-get install python3 python3-dev python3-pip
$ pip3 install django djangorestframework selenium
```
```console
$ git clone https://github.com/SWPP/ttrs-backend.git
```

#### Cors headers
On a development environment, you might run into the cors problem.
To resolve this, install django-cors-headers.
```console
$ pip3 install django-cors-headers
```

## Notice
#### Crawling in server machine
Installing chromium-browser and downgrading selenium seems to work.
```console
$ sudo apt-get install chromium-browser
$ pip3 uninstall selenium
$ pip3 install selenium==3.10
```

## APIs
For the specification, please see [**WIKI**](https://github.com/SWPP/ttrs-backend/wiki/RESTful-API)

## ttrs-frontend
https://github.com/SWPP/ttrs-frontend
