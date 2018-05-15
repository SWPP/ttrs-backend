from django.db import models

semester_choices = (('1학기', '1학기'), ('2학기', '2학기'), ('여름학기', '여름학기'), ('겨울학기', '겨울학기'))


class Crawler(models.Model):
    started = models.DateTimeField(auto_now_add=True)
    year = models.CharField(max_length=10)
    semester = models.CharField(max_length=10, choices=semester_choices)
    status = models.TextField()
    cancel_flag = models.BooleanField(default=False)

    def __str__(self):
        return '{}-{} {}'.format(self.year, self.semester, self.status)
