from ttrs.models import *
from manager.models import *

print('\033[1m'+'='*15+' Initialize '+'='*15+'\033[0m')
Evaluation.objects.all().delete()
Student.objects.all().delete()
Course.objects.all().delete()
Classroom.objects.all().delete()
Crawler.objects.all().delete()
print('\nSuccessfully cleaned model instances.')
