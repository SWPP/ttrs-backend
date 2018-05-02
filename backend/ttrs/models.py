from django.contrib.auth.models import User, UserManager
from django.db import models


class Student(User):
    objects = UserManager()

    college = models.ForeignKey('ttrs.College', related_name='students', on_delete=models.CASCADE)
    department = models.ForeignKey('ttrs.Department', related_name='students', on_delete=models.CASCADE, null=True, blank=True)
    major = models.ForeignKey('ttrs.Major', related_name='students', on_delete=models.CASCADE, null=True, blank=True)
    grade = models.PositiveSmallIntegerField()

    not_recommends = models.ManyToManyField('ttrs.Course', blank=True)


class Course(models.Model):
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=50)

    type = models.CharField(max_length=10)
    field = models.CharField(max_length=30, null=True, blank=True)
    grade = models.PositiveSmallIntegerField()
    credit = models.PositiveSmallIntegerField()

    college = models.ForeignKey('ttrs.College', related_name='courses', on_delete=models.CASCADE)
    department = models.ForeignKey('ttrs.Department', related_name='courses', on_delete=models.CASCADE, null=True, blank=True)
    major = models.ForeignKey('ttrs.Major', related_name='courses', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name


class Lecture(models.Model):
    course = models.ForeignKey('ttrs.Course', related_name='lectures', on_delete=models.CASCADE)
    time_slots = models.ManyToManyField('ttrs.TimeSlot', related_name='lectures')

    year = models.PositiveSmallIntegerField()
    semester = models.CharField(max_length=1)
    number = models.CharField(max_length=10)

    instructor = models.CharField(max_length=20)
    note = models.TextField(blank=True)

    def __str__(self):
        return '{}-{} ({}:{})'.format(self.course, self.instructor, self.year, self.semester)


class Evaluation(models.Model):
    author = models.ForeignKey('ttrs.Student', related_name='evauations', on_delete=models.DO_NOTHING)
    lecture = models.ForeignKey('ttrs.Lecture', related_name='evaluations', on_delete=models.CASCADE)
    rate = models.PositiveSmallIntegerField()
    comment = models.TextField()
    like_it = models.PositiveIntegerField()

    def __str__(self):
        return '{}-{}'.format(self.lecture, self.author)


class TimeTable(models.Model):
    owner = models.ForeignKey('ttrs.Student', related_name='time_tables', on_delete=models.CASCADE)
    type = models.CharField(max_length=10)

    title = models.CharField(max_length=100)
    memo = models.TextField()

    lectures = models.ManyToManyField('ttrs.Lecture', related_name='lectures', blank=True)

    def __str__(self):
        return '{}-{}[{}] ({})'.format(self.owner, self.title, self.type, self.lectures.count())


class TimeSlot(models.Model):
    start = models.DateTimeField()
    end = models.DateTimeField()

    classroom = models.ForeignKey('ttrs.Classroom', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        if self.classroom:
            return '{}~{} [{}]'.format(self.start.strftime('%a %I:%M'), self.end.strftime('%I:%M'), self.classroom)
        return '{}~{}'.format(self.start.strftime('%a %I:%M'), self.end.strftime('%I:%M'))


class Classroom(models.Model):
    building = models.CharField(max_length=10)
    room_no = models.CharField(max_length=10)

    def __str__(self):
        return '{}-{}'.format(self.building, self.room_no)


class College(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class Department(models.Model):
    college = models.ForeignKey('ttrs.College', related_name='departments', on_delete=models.CASCADE)
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class Major(models.Model):
    department = models.ForeignKey('ttrs.Department', related_name='majors', on_delete=models.CASCADE)
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name
